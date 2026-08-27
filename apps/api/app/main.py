import asyncio
from contextlib import asynccontextmanager
import json

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .adk_fleet import adk_runtime_status
from .adk_runtime import AdkExecutionService, AdkTraceRepository
from .memory import create_mission_repository
from .mission_service import MissionService
from .models import ApprovalRequest, CommandRequest, StartMissionRequest
from .nano_simulator import DEFAULT_CANDIDATES
from .security import ApprovalDenied, validate_approval

settings = get_settings()
repository = create_mission_repository(
    firestore_enabled=settings.firestore_enabled,
    project_id=settings.google_cloud_project,
    firestore_database=settings.firestore_database,
    demo_mode=settings.demo_mode,
)
service = MissionService(repository)
adk_trace_repository = AdkTraceRepository()
adk_execution = AdkExecutionService(adk_trace_repository)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
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
            "memory_backend_configured": repository.configured_backend}


@app.get("/api/architecture/proof")
def architecture_proof() -> dict:
    return {
        "implemented": ["four-agent visible trace", "deterministic nano simulator", "SSE events",
                        "fail-closed approval", "receipt hashing", "3D action contract",
                        "Firestore mission memory", "demo fallback"],
        "next_connectors": ["Gemini Live gateway", "synthetic image evidence"],
        "deployment_target": ["Cloud Run", "Secret Manager", "Cloud Logging"],
        "cloud_scope": "google_cloud_only",
    }


@app.get("/api/agentic/capabilities")
def capabilities() -> dict:
    return {"visible_agents": ["Evidence Scout", "Nano Designer", "Twin Simulator", "Safety Steward"],
            "inputs": ["text", "voice_gateway_planned", "synthetic_image_planned", "3d_selection"],
            "approval": {"voice_can_request": True, "voice_can_approve": False, "ui_confirmation_required": True}}


@app.get("/api/agentic/adk/proof")
def adk_proof() -> dict:
    """Judge-facing topology proof. This endpoint never triggers a billable model call."""
    return adk_runtime_status(settings.adk_enabled, settings.adk_model)


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
    if not repository.get(mission_id):
        raise HTTPException(404, "Mission not found")
    normalized = request.command.lower()
    action = "focus_clone" if "red clone" in normalized else "show_rejection" if "reject" in normalized else "compare_candidates"
    return {"accepted": True, "channel": request.channel, "scene_action": action,
            "approval_granted": False}


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
        "stores": ["missions", "mission_receipts", "approval_events", "resume_cursor"],
        "credentials_exposed": False,
        "standalone_memory_ui": False,
    }
