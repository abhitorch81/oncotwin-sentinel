import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.adk_fleet import (
    FLEET_AGENTS,
    FLEET_POLICY,
    OncoTwinAdkFleet,
    adk_capabilities,
    sanitized_mission_context,
)
from backend.app.config import Settings
from backend.app.main import app


client = TestClient(app)


def settings(**overrides):
    return Settings(_env_file=None, **overrides)


def test_primary_model_satisfies_hackathon_gemini_minimum():
    config = settings()
    assert config.gemini_model == "gemini-3.5-flash"
    assert config.hackathon_model_compliant is True
    assert settings(gemini_model="gemini-3.1-flash-live-preview").hackathon_model_compliant is False


def test_adk_capability_declares_real_framework_runtime_and_safety_boundary():
    payload = adk_capabilities(settings())
    assert payload["framework"] == "Google Agent Development Kit (ADK)"
    assert payload["orchestration"] == "SequentialAgent"
    assert payload["runtime"] == "Cloud Run"
    assert payload["agents"] == list(FLEET_AGENTS)
    assert payload["policy"] == FLEET_POLICY
    assert payload["model_compliant"] is True
    registry = client.get("/api/adk/registry").json()
    assert len(registry["agents"]) == 4
    assert {agent["tool_scope"] for agent in registry["agents"]} <= {
        "sanitized-read-only", "none", "proposal-only"
    }


def test_sanitized_adk_context_excludes_secrets_and_raw_evidence_payloads():
    context = sanitized_mission_context({
        "mission_id": "mission-1",
        "case_id": "feature_quality",
        "cohort": "LUAD",
        "status": "awaiting_approval",
        "approval_required": True,
        "writeback_approval_secret": "must-not-leak",
        "events": [{
            "type": "datahub_context", "agent": "Context Scout", "summary": "Grounded.",
            "evidence": {"token": "must-not-leak"},
        }],
    })
    serialized = str(context)
    assert "must-not-leak" not in serialized
    assert "writeback_approval_secret" not in serialized
    assert context["approval_required"] is True


def test_demo_adk_fleet_returns_four_agent_judge_trace_without_mutation():
    result = asyncio.run(OncoTwinAdkFleet(settings(demo_mode=True)).coordinate({
        "mission_id": "mission-1", "case_id": "feature_quality", "cohort": "LUAD",
        "status": "awaiting_approval", "approval_required": True, "events": [],
    }))
    assert result["framework"] == "Google ADK"
    assert result["execution_mode"] == "deterministic_demo"
    assert [event["agent"] for event in result["trace"]] == list(FLEET_AGENTS)
    assert result["policy"]["external_mutation_allowed"] is False
    assert result["policy"]["human_confirmation_required"] is True


def test_governed_investigation_contains_adk_trace_and_still_stops_for_approval():
    response = client.post("/api/agentic/commands", json={
        "utterance": "Start an ADK investigation",
        "modality": "text",
        "current_view": "mission",
        "case_id": "feature_quality",
        "cohort": "LUAD",
    })
    assert response.status_code == 200
    mission = response.json()["mission"]
    assert mission["status"] == "awaiting_approval"
    assert mission["approval_required"] is True
    assert mission["adk_fleet"]["orchestrator"] == "SequentialAgent"
    assert mission["adk_fleet"]["policy"]["approval_secret_available"] is False


def test_source_uses_adk_runner_sequential_and_llm_agents_not_name_only():
    root = Path(__file__).resolve().parents[2]
    source = (root / "backend" / "app" / "adk_fleet.py").read_text(encoding="utf-8")
    requirements = (root / "requirements.txt").read_text(encoding="utf-8")
    assert "from google.adk.agents import LlmAgent, SequentialAgent" in source
    assert "from google.adk.runners import Runner" in source
    assert "InMemorySessionService" in source
    assert "tools=[inspect_governed_mission]" in source
    assert "google-adk" in requirements


def test_health_and_frontend_expose_judge_visible_adk_compliance_proof():
    health = client.get("/api/health").json()
    assert health["hackathon_compliance"]["gemini_3_5_or_newer"] is True
    assert "Google ADK" in health["hackathon_compliance"]["agent_framework"]
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    client_js = (root / "frontend" / "assets" / "agentic-multimodal.js").read_text(encoding="utf-8")
    assert "ADK FLEET" in html
    assert "renderAdkTrace" in client_js
    assert "approvalSecret" not in client_js
