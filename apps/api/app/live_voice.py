"""Proof contract for governed Gemini 3.5 agent narration."""

from typing import Any


def _is_gemini_35_or_newer(model: str) -> bool:
    return model.startswith(("gemini-3.5", "gemini-3.6", "gemini-3.7"))


def voice_capability_proof(
    *, enabled: bool, reasoning_model: str,
    transcription_model: str = "gemini-3.5-transcribe-live-preview",
) -> dict[str, Any]:
    all_gemini_models_qualify = all(
        _is_gemini_35_or_newer(model)
        for model in (reasoning_model, transcription_model)
    )
    return {
        "enabled": enabled,
        "architecture": "gemini_3_5_live_transcription_with_adk_3_5",
        "qualifying_reasoning_model": reasoning_model,
        "transcription_model": transcription_model,
        "minimum_gemini_version_met": all_gemini_models_qualify,
        "all_gemini_models_meet_minimum_version": all_gemini_models_qualify,
        "transcription_role": "streaming_speech_to_text_only",
        "speech_input": "pcm_s16le_16000_websocket",
        "speech_output": "validated_text_rendered_by_google_cloud_tts",
        "spoken_content_source": "validated_agent_work_product",
        "barge_in": "gemini_3_5_vad_and_client_audio_cancel",
        "navigation_tools": sorted([
            "next_candidate", "previous_candidate", "select_candidate", "next_hour",
            "previous_hour", "set_hour", "play_timeline", "pause_timeline",
            "show_approval_boundary",
        ]),
        "separate_live_reasoning_model": False,
        "credentials_exposed": False,
        "voice_can_approve": False,
        "voice_can_persist_child_run": False,
    }
