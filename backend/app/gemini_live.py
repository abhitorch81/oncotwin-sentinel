"""Backend-only Gemini Live bridge with a deterministic command safety boundary."""
from __future__ import annotations

import asyncio
import base64
import binascii
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from starlette.websockets import WebSocketState

from .agentic_models import AgenticCommandRequest
from .agentic_router import route_agentic_command
from .config import Settings
from .mission_control import MissionManager


logger = logging.getLogger(__name__)
MAX_AUDIO_CHUNK_BYTES = 128 * 1024
SYSTEM_INSTRUCTION = """
You are the realtime voice of OncoTwin Sentinel, a synthetic oncology research
digital twin. Be concise, calm and evidence-first. Never diagnose, recommend
treatment, or claim an individual outcome. Clearly label projections and
uncertainty. You may explain what is visible, but you have no authority to
execute tools, approve a mission, reveal secrets, mutate data or take clinical
action. If asked to approve, authorize, commit, execute or write back, say that
voice cannot approve and a human must use the visible review gate. UI commands
are independently interpreted by a deterministic safety router.
""".strip()


def _merge_transcript(current: str, update: str) -> str:
    current, update = current.strip(), update.strip()
    if not update:
        return current
    if not current or update.startswith(current):
        return update
    if current.endswith(update):
        return current
    return f"{current} {update}".strip()


def extract_live_events(response: Any) -> list[dict[str, Any]]:
    """Convert SDK response objects into the small browser protocol."""
    events: list[dict[str, Any]] = []
    content = getattr(response, "server_content", None)
    model_turn = getattr(content, "model_turn", None) if content else None
    for part in getattr(model_turn, "parts", None) or []:
        inline = getattr(part, "inline_data", None)
        data = getattr(inline, "data", None) if inline else None
        mime_type = getattr(inline, "mime_type", "") if inline else ""
        if data and str(mime_type).startswith("audio/"):
            events.append({
                "type": "audio",
                "data": base64.b64encode(bytes(data)).decode("ascii"),
                "mime_type": str(mime_type),
                "sample_rate": 24000,
            })

    input_transcription = getattr(content, "input_transcription", None) if content else None
    output_transcription = getattr(content, "output_transcription", None) if content else None
    if getattr(input_transcription, "text", None):
        events.append({"type": "input_transcript", "text": input_transcription.text})
    if getattr(output_transcription, "text", None):
        events.append({"type": "output_transcript", "text": output_transcription.text})
    if content and getattr(content, "interrupted", False):
        events.append({"type": "interrupted"})
    if content and getattr(content, "turn_complete", False):
        events.append({"type": "turn_complete"})
    if getattr(response, "go_away", None):
        events.append({"type": "reconnect_required", "reason": "session_rotation"})
    return events


class GeminiLiveBridge:
    def __init__(self, settings: Settings, mission_manager: MissionManager):
        self.settings = settings
        self.mission_manager = mission_manager
        self._send_lock = asyncio.Lock()
        self._context: dict[str, str] = {
            "current_view": "mission", "case_id": "feature_quality", "cohort": "LUAD"
        }
        self._input_transcript = ""
        self._last_routed_transcript = ""

    def _client(self) -> genai.Client:
        if self.settings.gemini_live_use_vertexai:
            return genai.Client(
                vertexai=True,
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )
        return genai.Client(api_key=self.settings.google_api_key)

    def _config(self) -> types.LiveConnectConfig:
        return types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.settings.gemini_live_voice,
                    )
                )
            ),
            system_instruction=types.Content(parts=[types.Part(text=SYSTEM_INSTRUCTION)]),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            realtime_input_config=types.RealtimeInputConfig(
                turn_coverage="TURN_INCLUDES_ONLY_ACTIVITY",
            ),
        )

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        if websocket.client_state != WebSocketState.CONNECTED:
            return
        async with self._send_lock:
            await websocket.send_json(payload)

    def _update_context(self, raw: Any) -> None:
        if not isinstance(raw, dict):
            return
        for key, default, limit in (
            ("current_view", "mission", 40), ("case_id", "feature_quality", 80), ("cohort", "LUAD", 32)
        ):
            value = str(raw.get(key, self._context.get(key, default))).strip()[:limit]
            if value:
                self._context[key] = value

    async def _route_transcript(self, websocket: WebSocket, transcript: str) -> None:
        normalized = " ".join(transcript.split())
        if len(normalized) < 2 or normalized == self._last_routed_transcript:
            return
        self._last_routed_transcript = normalized
        request = AgenticCommandRequest(
            utterance=normalized,
            modality="voice",
            current_view=self._context["current_view"],
            case_id=self._context["case_id"],
            cohort=self._context["cohort"],
        )
        result = await route_agentic_command(request, self.mission_manager)
        await self._send(websocket, {"type": "command_result", "command": result.model_dump(mode="json")})

    async def _client_to_gemini(self, websocket: WebSocket, session: Any) -> None:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "context":
                self._update_context(message.get("context"))
            elif message_type == "audio":
                encoded = message.get("data", "")
                try:
                    chunk = base64.b64decode(encoded, validate=True)
                except (binascii.Error, ValueError):
                    await self._send(websocket, {"type": "error", "code": "invalid_audio"})
                    continue
                if not chunk or len(chunk) > MAX_AUDIO_CHUNK_BYTES:
                    await self._send(websocket, {"type": "error", "code": "audio_chunk_rejected"})
                    continue
                await session.send_realtime_input(
                    audio=types.Blob(
                        data=chunk,
                        mime_type=f"audio/pcm;rate={self.settings.gemini_live_input_sample_rate}",
                    )
                )
            elif message_type == "text":
                text = str(message.get("text", "")).strip()[:1000]
                self._update_context(message.get("context"))
                if text:
                    await self._route_transcript(websocket, text)
                    await session.send_realtime_input(text=text)
            elif message_type == "end_turn":
                await session.send_realtime_input(audio_stream_end=True)
            elif message_type == "ping":
                await self._send(websocket, {"type": "pong"})
            elif message_type == "stop":
                return
            else:
                await self._send(websocket, {"type": "error", "code": "unsupported_message"})

    async def _gemini_to_client(self, websocket: WebSocket, session: Any) -> None:
        while True:
            received = False
            async for response in session.receive():
                received = True
                for event in extract_live_events(response):
                    if event["type"] == "input_transcript":
                        self._input_transcript = _merge_transcript(self._input_transcript, event["text"])
                        event["text"] = self._input_transcript
                    await self._send(websocket, event)
                    if event["type"] == "turn_complete":
                        transcript = self._input_transcript
                        self._input_transcript = ""
                        await self._route_transcript(websocket, transcript)
            if not received:
                return

    async def serve(self, websocket: WebSocket) -> None:
        client = self._client()
        async with client.aio.live.connect(
            model=self.settings.gemini_live_model,
            config=self._config(),
        ) as session:
            await self._send(websocket, {
                "type": "connected",
                "model": self.settings.gemini_live_model,
                "voice": self.settings.gemini_live_voice,
                "input_sample_rate": self.settings.gemini_live_input_sample_rate,
                "output_sample_rate": self.settings.gemini_live_output_sample_rate,
                "safety": {"voice_approval_allowed": False, "clinical_action_allowed": False},
            })
            client_task = asyncio.create_task(self._client_to_gemini(websocket, session))
            model_task = asyncio.create_task(self._gemini_to_client(websocket, session))
            done, pending = await asyncio.wait(
                {client_task, model_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()


def build_gemini_live_router(settings: Settings, mission_manager: MissionManager) -> APIRouter:
    router = APIRouter(tags=["gemini-live"])

    @router.websocket("/api/agentic/live")
    async def gemini_live_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        if not settings.gemini_live_ready:
            await websocket.send_json({
                "type": "unavailable",
                "reason": "disabled" if not settings.gemini_live_enabled else "configuration_required",
                "fallback": "browser_speech_plus_local_fast",
            })
            await websocket.close(code=1013)
            return
        try:
            async with asyncio.timeout(settings.gemini_live_max_session_seconds):
                await GeminiLiveBridge(settings, mission_manager).serve(websocket)
        except WebSocketDisconnect:
            return
        except TimeoutError:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({"type": "reconnect_required", "reason": "session_limit"})
                await websocket.close(code=1000)
        except Exception as exc:  # Keep provider errors and credentials server-side.
            logger.warning("Gemini Live session stopped safely: %s", type(exc).__name__)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "type": "unavailable", "reason": "live_connection_failed",
                    "fallback": "browser_speech_plus_local_fast",
                })
                await websocket.close(code=1011)

    return router
