import asyncio
from contextlib import asynccontextmanager
import json

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from .config import get_settings
from .bounded_reruns import build_bounded_rerun_preview, is_bounded_rerun_command
from .child_reruns import persist_bounded_rerun_child
from .contextual_explanations import build_contextual_explanation
from .eligibility import build_eligibility_proof, meets_minimum_gemini_version
from .adk_fleet import adk_runtime_status
from .adk_runtime import AdkExecutionService, create_adk_trace_repository
from .memory import create_mission_repository
from .image_evidence import analyze_synthetic_image
from .mission_service import MissionService
from .live_voice import voice_capability_proof
from .live_voice_gateway import run_live_voice_session
from .models import ApprovalRequest, CommandRequest, PersistRerunRequest, StartMissionRequest, VoiceSynthesisRequest
from .nano_simulator import DEFAULT_CANDIDATES
from .security import ApprovalDenied, validate_approval
from .speech_service import VOICE_NAME, synthesize_agent_speech

settings = get_settings()
repository = create_mission_repository(
    firestore_enabled=settings.firestore_enabled,
    project_id=settings.google_cloud_project,
    firestore_database=settings.firestore_database,
    demo_mode=settings.demo_mode,
)
service = MissionService(repository)
adk_trace_repository = create_adk_trace_repository(
    firestore_enabled=settings.firestore_enabled,
    project_id=settings.google_cloud_project,
    firestore_database=settings.firestore_database,
    demo_mode=settings.demo_mode,
)
adk_execution = AdkExecutionService(adk_trace_repository)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await adk_trace_repository.close()
    repository.close()


app = FastAPI(title=settings.app_name, version=settings.app_version,
              description="Synthetic research-only agentic oncology digital twin.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "app_name": settings.app_name, "ui_version": settings.app_version,
            "edition": "google-native-milestone-1", "mode": "demo" if settings.demo_mode else "live",
            "medical_use": "synthetic_research_only", "human_approval_required": True,
            "adk_enabled": settings.adk_enabled,
            "gemini_model": settings.adk_model,
            "governed_voice_enabled": settings.governed_voice_enabled,
            "live_transcription_model": settings.live_voice_model,
            "all_gemini_models_meet_minimum_version": all(
                meets_minimum_gemini_version(model)
                for model in (settings.adk_model, settings.live_voice_model)
            ),
            "gemini_access": "vertex_ai" if settings.google_genai_use_vertexai else "unverified",
            "minimum_gemini_version_met": meets_minimum_gemini_version(settings.adk_model),
            "memory_backend_configured": repository.configured_backend,
            "adk_trace_backend_configured": adk_trace_repository.configured_backend}


@app.get("/api/architecture/proof")
def architecture_proof() -> dict:
    return {
        "implemented": ["Gemini 3.5 Flash on Vertex AI", "Gemini 3.5 synthetic image evidence", "governed agent narration", "four-agent visible trace", "deterministic nano simulator", "SSE events",
                        "fail-closed approval", "receipt hashing", "3D action contract",
                        "Firestore mission memory", "Firestore ADK traces", "demo fallback"],
        "next_connectors": [],
        "deployment_target": ["Cloud Run", "Secret Manager", "Cloud Logging"],
        "cloud_scope": "google_cloud_only",
    }


@app.get("/api/agentic/capabilities")
def capabilities() -> dict:
    return {"visible_agents": ["Evidence Scout", "Nano Designer", "Twin Simulator", "Safety Steward"],
            "inputs": ["text", "governed_voice", "synthetic_image", "3d_selection", "simulation_time"],
            "approval": {"voice_can_request": True, "voice_can_approve": False, "ui_confirmation_required": True}}


@app.get("/api/live/voice/proof")
def live_voice_proof() -> dict:
    """Judge-facing capability proof; opening this endpoint never starts a Live session."""
    return {**voice_capability_proof(
        enabled=settings.governed_voice_enabled,
        reasoning_model=settings.adk_model,
        transcription_model=settings.live_voice_model,
    ), "renderer": "google_cloud_text_to_speech", "voice": VOICE_NAME}


@app.websocket("/api/live/voice/{mission_id}")
async def live_voice_session(websocket: WebSocket, mission_id: str) -> None:
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.origins:
        await websocket.close(code=1008)
        return
    mission = await asyncio.to_thread(repository.get, mission_id)
    if not mission or not settings.governed_voice_enabled:
        await websocket.close(code=1008)
        return
    await run_live_voice_session(
        websocket,
        mission=mission,
        project_id=settings.google_cloud_project,
        location=settings.live_voice_location,
        model=settings.live_voice_model,
    )


@app.post("/api/voice/synthesize")
async def synthesize_voice(request: VoiceSynthesisRequest) -> Response:
    if not settings.governed_voice_enabled:
        raise HTTPException(503, "Governed voice is disabled")
    try:
        audio = await asyncio.to_thread(synthesize_agent_speech, request.text)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store", "X-Voice-Renderer": VOICE_NAME},
    )


@app.get("/api/agentic/adk/proof")
def adk_proof() -> dict:
    """Judge-facing topology proof. This endpoint never triggers a billable model call."""
    return adk_runtime_status(settings.adk_enabled, settings.adk_model)


@app.get("/api/eligibility/proof")
def eligibility_proof() -> dict:
    """Judge-facing configuration proof; it never triggers a billable model call."""
    adk_status = adk_runtime_status(settings.adk_enabled, settings.adk_model)
    return build_eligibility_proof(
        model=settings.adk_model,
        vertex_ai_enabled=settings.google_genai_use_vertexai,
        adk_status=adk_status,
        firestore_configured=repository.configured_backend == "firestore",
        cloud_run_target=settings.app_env == "production",
    )


@app.get("/api/nano/candidates")
def candidates() -> list[dict]:
    return [candidate.__dict__ for candidate in DEFAULT_CANDIDATES]


@app.post("/api/nano/missions/start")
async def start_mission(request: StartMissionRequest, background_tasks: BackgroundTasks) -> dict:
    mission = await asyncio.to_thread(service.start, request.prompt)
    await adk_execution.prepare(mission.id, settings.adk_model, settings.adk_enabled)
    if settings.adk_enabled:
        background_tasks.add_task(
            adk_execution.run,
            mission.id,
            request.prompt,
            settings.adk_model,
            len(mission.receipt.prior_memory_used),
        )
    return mission.model_dump()


@app.get("/api/nano/missions/{mission_id}/adk-trace")
async def adk_trace(mission_id: str) -> dict:
    if not await asyncio.to_thread(repository.get, mission_id):
        raise HTTPException(404, "Mission not found")
    trace = await adk_trace_repository.get(mission_id)
    if not trace:
        raise HTTPException(404, "ADK trace not initialized")
    return trace.model_dump()


@app.get("/api/nano/missions/{mission_id}/adk-events")
async def adk_events(mission_id: str, request: Request) -> StreamingResponse:
    """Stream privacy-safe ADK node/tool metadata to the 3D mission theatre."""
    if not await asyncio.to_thread(repository.get, mission_id):
        raise HTTPException(404, "Mission not found")

    async def stream():
        cursor = 0
        while True:
            if await request.is_disconnected():
                return
            trace = await adk_trace_repository.get(mission_id)
            if trace is None:
                yield f"event: status\ndata: {json.dumps({'status': 'queued'})}\n\n"
                await asyncio.sleep(.2)
                continue
            while cursor < len(trace.events):
                event = trace.events[cursor]
                cursor += 1
                yield f"event: adk\ndata: {json.dumps(event.model_dump())}\n\n"
            yield f"event: status\ndata: {json.dumps({'status': trace.status, 'model': trace.model})}\n\n"
            if trace.status in {"disabled", "succeeded", "fallback"}:
                return
            await asyncio.sleep(.2)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/nano/missions/{mission_id}")
def get_mission(mission_id: str) -> dict:
    mission = repository.get(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    return mission.model_dump()


@app.post("/api/nano/missions/{mission_id}/evidence/images/analyze")
async def analyze_image_evidence(
    mission_id: str,
    file: UploadFile = File(...),
    selected_candidate_id: str | None = Form(default=None),
    simulation_hour: int = Form(default=24),
) -> dict:
    mission = await asyncio.to_thread(repository.get, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    if selected_candidate_id not in {None, "A", "B", "C"}:
        raise HTTPException(400, "Selected candidate must be A, B, or C")
    if not 0 <= simulation_hour <= 24:
        raise HTTPException(400, "Simulation hour must be between 0 and 24")
    data = await file.read(5 * 1024 * 1024 + 1)
    try:
        recent_context = await asyncio.to_thread(repository.recent_receipt_context, 4)
        current_prefix = mission.receipt.receipt_sha256[:12] if mission.receipt else ""
        prior_context = [
            item for item in recent_context
            if item.get("receipt_sha256_prefix") != current_prefix
        ][-3:]
        result = await asyncio.to_thread(
            analyze_synthetic_image,
            data=data,
            filename=file.filename,
            mime_type=file.content_type or "",
            mission=mission,
            selected_candidate_id=selected_candidate_id,
            simulation_hour=simulation_hour,
            prior_receipts=prior_context,
            project_id=settings.google_cloud_project,
            location=settings.google_cloud_location,
            model=settings.adk_model,
        )
        await asyncio.to_thread(
            repository.record_image_evidence,
            result.model_dump(mode="json"),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Gemini visual evidence analysis failed ({type(exc).__name__})") from exc
    return result.model_dump(mode="json")


@app.get("/api/nano/missions/{mission_id}/events")
async def mission_events(mission_id: str) -> StreamingResponse:
    mission = repository.get(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")

    async def stream():
        for event in mission.events:
            yield f"event: agent\ndata: {json.dumps(event.model_dump())}\n\n"
            await asyncio.sleep(.35)
        yield f"event: mission\ndata: {json.dumps({'state': mission.state})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/nano/missions/{mission_id}/commands")
def command(mission_id: str, request: CommandRequest) -> dict:
    mission = repository.get(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    try:
        if is_bounded_rerun_command(request.command):
            preview = build_bounded_rerun_preview(
                mission,
                command=request.command,
                selected_candidate_id=request.selected_candidate_id,
                channel=request.channel,
            )
            return preview.model_dump()
        image_evidence = None
        if request.image_evidence_id:
            image_evidence = repository.get_image_evidence(request.image_evidence_id)
            if not image_evidence:
                raise ValueError("Image evidence is unavailable for this mission")
        explanation = build_contextual_explanation(
            mission,
            question=request.command,
            selected_candidate_id=request.selected_candidate_id,
            simulation_hour=request.simulation_hour,
            channel=request.channel,
            image_evidence=image_evidence,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return explanation.model_dump()


@app.post("/api/nano/missions/{mission_id}/reruns/persist")
def persist_rerun(mission_id: str, request: PersistRerunRequest) -> dict:
    parent = repository.get(mission_id)
    if not parent:
        raise HTTPException(404, "Parent mission not found")
    try:
        child = persist_bounded_rerun_child(repository, parent, request)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return child.model_dump()


@app.post("/api/nano/missions/{mission_id}/request-approval")
def request_approval(mission_id: str) -> dict:
    mission = repository.get(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    mission.approval_requested = True
    repository.save(mission)
    return {"requested": True, "state": mission.state, "approval_granted": False}


@app.post("/api/nano/missions/{mission_id}/approve")
def approve(mission_id: str, request: ApprovalRequest) -> dict:
    mission = repository.get(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    try:
        validate_approval(request.channel, request.confirmation)
    except ApprovalDenied as exc:
        raise HTTPException(403, str(exc)) from exc
    mission.state = "approved"
    mission.approved_by = request.actor
    repository.record_approval(mission, request.actor, "approved", request.channel)
    return {"approved": True, "mission_id": mission.id, "approved_by": request.actor}


@app.get("/api/memory/proof")
def memory_proof() -> dict:
    """Judge-facing persistence proof with no connection details or sensitive payloads."""
    return {
        **repository.proof(),
        "stores": ["missions", "mission_receipts", "approval_events", "resume_cursor",
                   "adk_traces", "image_evidence"],
        "adk_trace_backend": adk_trace_repository.configured_backend,
        "credentials_exposed": False,
        "standalone_memory_ui": False,
    }
