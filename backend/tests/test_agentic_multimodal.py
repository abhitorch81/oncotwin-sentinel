from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def command(utterance: str, modality: str = "text", **overrides):
    payload = {
        "utterance": utterance,
        "modality": modality,
        "current_view": "mission",
        "case_id": "cancer_progression",
        "cohort": "LUAD",
        **overrides,
    }
    return client.post("/api/agentic/commands", json=payload)


def test_agentic_capabilities_are_honest_about_active_and_planned_lanes():
    response = client.get("/api/agentic/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signature_demo"] == "Show me why the resistant clone is red."
    assert payload["lanes"]["gemini_live"].startswith("planned integration")
    assert payload["safety"]["voice_approval_allowed"] is False
    assert payload["safety"]["external_mutations_from_command_router"] is False


def test_signature_command_focuses_real_3d_clone_and_explains_color_rule():
    response = command("Show me why the resistant clone is red.", "voice")
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "focus_clone"
    assert payload["lane"] == "local_fast"
    assert payload["safety"]["external_mutation_performed"] is False
    assert [action["type"] for action in payload["ui_actions"]] == [
        "switch_view", "focus_clone", "open_evidence"
    ]
    assert payload["evidence"][0]["value"] == "risk_score >= 0.85 → red"
    assert "not a diagnosis" in payload["spoken_response"]


def test_voice_approval_can_only_reveal_visible_human_gate():
    response = command("Approve and execute the writeback now", "voice")
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "request_approval"
    assert payload["mission"] is None
    assert payload["safety"] == {
        "research_only": True,
        "clinical_action_allowed": False,
        "voice_approval_allowed": False,
        "external_mutation_performed": False,
        "human_confirmation_required": True,
    }
    assert [action["type"] for action in payload["ui_actions"]] == [
        "switch_view", "open_approval_panel"
    ]


def test_anatomy_and_timepoint_commands_have_deterministic_scene_actions():
    anatomy = command("Focus on the liver").json()
    assert anatomy["intent"] == "focus_anatomy"
    assert anatomy["ui_actions"][-1] == {"type": "focus_anatomy", "anatomy": "liver"}

    timepoint = command("Show generation 2").json()
    assert timepoint["intent"] == "set_timepoint"
    assert timepoint["ui_actions"][-1] == {"type": "set_timepoint", "generation": 2}


def test_investigation_stops_at_governance_without_external_mutation():
    response = command("Start an investigation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "start_investigation"
    assert payload["lane"] == "investigation"
    assert payload["mission"]["status"] == "awaiting_approval"
    assert payload["mission"]["approval_required"] is True
    assert payload["safety"]["external_mutation_performed"] is False


def test_multimodal_ui_connects_voice_text_and_threejs_without_autoclicking_approval():
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (root / "frontend" / "assets" / "app.js").read_text(encoding="utf-8")
    agentic_js = (root / "frontend" / "assets" / "agentic-multimodal.js").read_text(encoding="utf-8")
    evolution_js = (root / "frontend" / "assets" / "evolution3d.js").read_text(encoding="utf-8")
    assert 'id="agenticCommandCenter"' in html
    assert 'id="twin3d"' in html
    assert "SpeechRecognition" in agentic_js
    assert "speechSynthesis" in agentic_js
    assert "/api/agentic/commands" in agentic_js
    assert "oncotwin:agentic-action" in app_js
    assert "focusClone" in evolution_js
    assert "approveMission.click" not in agentic_js
    assert "approveWriteback.click" not in agentic_js
