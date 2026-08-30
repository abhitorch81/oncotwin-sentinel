"""Gemini 3.5 streaming transcription for the governed voice interface.

Microphone audio is transcribed by Gemini 3.5. Final text returns to the browser
and enters the same bounded command route as typed input. Scientific reasoning stays
inside the Google ADK Gemini 3.5 workflow. Only validated text is rendered as speech.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)

NAVIGATION_ACTIONS = {
    "next_candidate", "previous_candidate", "select_candidate", "next_hour",
    "previous_hour", "set_hour", "play_timeline", "pause_timeline",
    "show_approval_boundary",
}


def normalize_navigation(arguments: dict[str, Any]) -> dict[str, Any]:
    """Policy guard retained for command/navigation validation."""
    action = str(arguments.get("action", "")).strip().lower()
    if action not in NAVIGATION_ACTIONS:
        raise ValueError("Unsupported voice navigation action")
    result: dict[str, Any] = {"action": action}
    if action == "select_candidate":
        candidate_id = str(arguments.get("candidate_id", "")).upper()
        if candidate_id not in {"A", "B", "C"}:
            raise ValueError("Candidate must be A, B, or C")
        result["candidate_id"] = candidate_id
    if action == "set_hour":
        hour = int(arguments.get("hour", -1))
        if not 0 <= hour <= 24:
            raise ValueError("Simulation hour must be between 0 and 24")
        result["hour"] = hour
    return result


async def run_live_voice_session(
    websocket: WebSocket,
    *,
    mission: Any,
    project_id: str,
    location: str,
    model: str,
) -> None:
    from google import genai
    from google.genai import types

    await websocket.accept()
    if not project_id:
        await websocket.send_json({
            "type": "error",
            "detail": "GOOGLE_CLOUD_PROJECT is not configured on the API server",
        })
        await websocket.close(code=1011)
        return

    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription=types.AudioTranscriptionConfig(
            language_codes=[],
            custom_vocabulary=[
                "OncoTwin", "SYN-R7", "Aster-48", "Brimstone-92", "Brimstone-70",
                "Calyx-61", "nanoparticle", "tumour", "liver accumulation",
                "kidney accumulation", "Safety Steward",
            ],
            mode="SMART",
        ),
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            await websocket.send_json({
                "type": "ready",
                "transcription_model": model,
                "authority_model": "gemini-3.5-flash",
                "renderer": "google_cloud_text_to_speech",
            })

            async def browser_to_gemini() -> None:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        return
                    if message.get("bytes") is not None:
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=message["bytes"],
                                mime_type="audio/pcm;rate=16000",
                            )
                        )
                        continue
                    raw = message.get("text")
                    if not raw:
                        continue
                    payload = json.loads(raw)
                    if payload.get("type") == "interrupt":
                        await websocket.send_json({"type": "interrupted"})

            async def gemini_to_browser() -> None:
                last_final = ""
                async for response in session.receive():
                    server_content = getattr(response, "server_content", None)
                    if not server_content:
                        continue
                    interim = getattr(server_content, "interim_input_transcription", None)
                    interim_text = str(getattr(interim, "text", "") or "").strip()
                    if interim_text:
                        await websocket.send_json({
                            "type": "input_transcript",
                            "text": interim_text,
                            "final": False,
                        })
                    final = getattr(server_content, "input_transcription", None)
                    final_text = str(getattr(final, "text", "") or "").strip()
                    if final_text and final_text != last_final:
                        last_final = final_text
                        await websocket.send_json({
                            "type": "input_transcript",
                            "text": final_text,
                            "final": True,
                        })
                    if getattr(server_content, "turn_complete", False):
                        await websocket.send_json({"type": "turn_complete"})

            tasks = [
                asyncio.create_task(browser_to_gemini()),
                asyncio.create_task(gemini_to_browser()),
            ]
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    task.result()
                except (WebSocketDisconnect, RuntimeError) as exc:
                    if "disconnect" not in str(exc).lower():
                        raise
    except WebSocketDisconnect:
        return
    except Exception as exc:
        logger.exception("Gemini 3.5 transcription session failed for %s", mission.id)
        try:
            await websocket.send_json({
                "type": "error",
                "detail": f"{type(exc).__name__}: {str(exc)[:180]}",
            })
            await websocket.close(code=1011)
        except Exception:
            return
