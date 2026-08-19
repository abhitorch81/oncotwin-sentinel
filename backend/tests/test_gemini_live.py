from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.agentic_router import agentic_capabilities
from backend.app.config import Settings
from backend.app.gemini_live import (
    SYSTEM_INSTRUCTION,
    _merge_transcript,
    build_gemini_live_router,
    extract_live_events,
)


def settings(**overrides):
    return Settings(_env_file=None, **overrides)


def test_live_is_fail_safe_and_disabled_without_explicit_configuration():
    config = settings()
    assert config.gemini_live_ready is False
    live = agentic_capabilities(config)["lanes"]["gemini_live"]
    assert live["status"] == "disabled"
    assert live["fallback"] == "browser_speech_plus_local_fast"


def test_live_requires_server_side_credentials_for_selected_provider():
    developer = settings(gemini_live_enabled=True, gemini_live_use_vertexai=False)
    assert developer.gemini_live_ready is False
    assert settings(
        gemini_live_enabled=True,
        gemini_live_use_vertexai=False,
        google_api_key="test-only-key",
    ).gemini_live_ready is True
    assert settings(
        gemini_live_enabled=True,
        gemini_live_use_vertexai=True,
        google_cloud_project="test-project",
    ).gemini_live_ready is True


def test_disabled_websocket_declares_fallback_and_closes_without_provider_call():
    app = FastAPI()
    app.include_router(build_gemini_live_router(settings(), object()))
    client = TestClient(app)
    with client.websocket_connect("/api/agentic/live") as socket:
        payload = socket.receive_json()
        assert payload == {
            "type": "unavailable",
            "reason": "disabled",
            "fallback": "browser_speech_plus_local_fast",
        }


def test_sdk_messages_map_to_small_secret_free_browser_protocol():
    audio = SimpleNamespace(data=b"\x01\x02", mime_type="audio/pcm;rate=24000")
    part = SimpleNamespace(inline_data=audio)
    content = SimpleNamespace(
        model_turn=SimpleNamespace(parts=[part]),
        input_transcription=SimpleNamespace(text="focus on the liver"),
        output_transcription=SimpleNamespace(text="Focusing the synthetic liver."),
        interrupted=True,
        turn_complete=True,
    )
    response = SimpleNamespace(server_content=content, go_away=None)
    events = extract_live_events(response)
    assert [event["type"] for event in events] == [
        "audio", "input_transcript", "output_transcript", "interrupted", "turn_complete"
    ]
    assert events[0]["data"] == "AQI="
    assert events[0]["sample_rate"] == 24000


def test_transcript_merging_handles_cumulative_and_delta_updates():
    assert _merge_transcript("show me", "show me why") == "show me why"
    assert _merge_transcript("show me why", "the clone is red") == "show me why the clone is red"
    assert _merge_transcript("show me why", "why") == "show me why"


def test_live_system_prompt_denies_clinical_and_approval_authority():
    prompt = SYSTEM_INSTRUCTION.lower()
    assert "never diagnose" in prompt
    assert "no authority" in prompt
    assert "voice cannot approve" in prompt
    assert "deterministic safety router" in prompt


def test_frontend_uses_pcm_worklet_native_playback_and_no_browser_key():
    root = Path(__file__).resolve().parents[2]
    client_js = (root / "frontend" / "assets" / "agentic-multimodal.js").read_text(encoding="utf-8")
    worklet = (root / "frontend" / "assets" / "pcm-capture-worklet.js").read_text(encoding="utf-8")
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "new WebSocket(socketUrl())" in client_js
    assert "AudioWorkletNode" in client_js
    assert "echoCancellation:true" in client_js
    assert "stopPlayback" in client_js
    assert "Int16Array" in worklet
    assert "targetSampleRate:16000" in client_js
    assert 'id="agenticLiveBadge"' in html
    assert "GOOGLE_API_KEY" not in client_js
    assert "GEMINI_API_KEY" not in client_js
