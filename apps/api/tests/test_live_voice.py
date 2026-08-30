from apps.api.app.live_voice import voice_capability_proof
from apps.api.app.live_voice_gateway import normalize_navigation
from apps.api.app.speech_service import synthesize_agent_speech
import pytest


def test_voice_capability_proof_exposes_no_credentials_or_authority() -> None:
    proof = voice_capability_proof(
        enabled=True,
        reasoning_model="gemini-3.5-flash",
    )
    assert proof["enabled"] is True
    assert proof["qualifying_reasoning_model"] == "gemini-3.5-flash"
    assert proof["minimum_gemini_version_met"] is True
    assert proof["all_gemini_models_meet_minimum_version"] is True
    assert proof["transcription_model"] == "gemini-3.5-transcribe-live-preview"
    assert proof["transcription_role"] == "streaming_speech_to_text_only"
    assert proof["credentials_exposed"] is False
    assert proof["voice_can_approve"] is False
    assert proof["voice_can_persist_child_run"] is False


def test_voice_proof_rejects_pre_35_gemini_models() -> None:
    proof = voice_capability_proof(
        enabled=True,
        reasoning_model="gemini-3.5-flash",
        transcription_model="gemini-3.1-flash-live-preview",
    )
    assert proof["all_gemini_models_meet_minimum_version"] is False


def test_voice_navigation_is_bounded() -> None:
    assert normalize_navigation({"action": "next_candidate"}) == {
        "action": "next_candidate"
    }
    assert normalize_navigation({"action": "select_candidate", "candidate_id": "b"}) == {
        "action": "select_candidate", "candidate_id": "B"
    }
    assert normalize_navigation({"action": "set_hour", "hour": 18}) == {
        "action": "set_hour", "hour": 18
    }
    with pytest.raises(ValueError):
        normalize_navigation({"action": "approve"})
    with pytest.raises(ValueError):
        normalize_navigation({"action": "set_hour", "hour": 25})


def test_speech_renderer_rejects_empty_or_oversized_text_before_cloud_call() -> None:
    with pytest.raises(ValueError):
        synthesize_agent_speech("   ")
    with pytest.raises(ValueError):
        synthesize_agent_speech("x" * 2001)
