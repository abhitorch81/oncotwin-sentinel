import os
from pathlib import Path

os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
    assert response.json()["ui_version"] == "10.1.0"


def test_judge_ui_uses_ingested_datahub_schema_and_exact_repair():
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (root / "frontend" / "assets" / "app.js").read_text(encoding="utf-8")
    assert "gene_expression_summary.gene STRING" in html
    assert "mean_expression FLOAT64" in html
    assert "expression_zscore" not in html + js
    assert "cell_cluster_id" not in html + js
    assert "COALESCE(AVG(IF(gene = 'MKI67'" in js
    assert "urn:li:dataPlatform:bigquery" in js


def test_verified_replay_is_visible_and_survives_backend_instance_loss():
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (root / "frontend" / "assets" / "app.js").read_text(encoding="utf-8")
    assert 'id="replayMission"' in html
    assert "localStorage.setItem(REPLAY_CACHE_KEY" in js
    assert "events=cachedEvents" in js
    assert "resetMissionVisualsForReplay" in js
    assert "REPLAYING ${i+1}/${events.length}" in js
    assert "zero write operations" in js


def test_agent_workflow_has_guarded_writeback():
    response = client.post("/api/agents/run", json={"question": "Which progression assets are trustworthy?"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["traces"]) == 6
    assert payload["proposal"]["requires_approval"] is True
    assert payload["generated_artifacts"]["dbt"]
    assert payload["context_fingerprint"]
    assert payload["traces"][-2]["agent"] == "Repair Engineer"
    assert payload["traces"][-1]["status"] == "blocked"
    assert [step["scene_cue"] for step in payload["traces"]] == [
        "catalog-scan",
        "quality-warning",
        "lineage-pulse",
        "risk-focus",
        "lineage-pulse",
        "governance-lock",
    ]


def test_datahub_capability_proof():
    response = client.get("/api/datahub/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert "list_schema_fields" in payload["mcp"]["read_tools"]
    assert "datahub-lineage" in payload["skills"]
    assert payload["agent_context_kit"]["llm"] == "Google Gemini / Vertex AI"


def test_judge_proof_endpoint_exposes_auditable_read_only_evidence():
    response = client.get("/api/datahub/proof")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "deterministic-demo"
    assert payload["transport"] == "stdio/self-hosted MCP"
    assert payload["total_tools"] == 6
    assert payload["all_tools_passed"] is True
    assert payload["mutation_performed"] is False
    assert payload["human_approval_boundary"] is True
    assert "urn:li:dataPlatform:bigquery" in payload["asset_urn"]
    assert [item["tool"] for item in payload["evidence"]] == [
        "search",
        "get_entities",
        "list_schema_fields",
        "get_lineage_upstream",
        "get_lineage_downstream",
        "get_dataset_queries",
    ]
    assert payload["receipt_sha256"]


def test_every_condition_has_unique_datahub_asset_and_six_call_receipt():
    expected = {
        "feature_quality": "progression_features",
        "cancer_progression": "tumour_state_transitions",
        "model_drift": "cohort_drift_metrics",
        "schema_mutation": "genomic_schema_contract_events",
        "biomarker_discordance": "multi_omic_biomarker_evidence",
        "protein_conformation": "protein_conformation_states",
        "microenvironment_escape": "spatial_microenvironment_states",
    }
    urns = set()
    for case_id, asset_name in expected.items():
        response = client.get(f"/api/datahub/proof?case_id={case_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["case_id"] == case_id
        assert payload["asset_name"] == asset_name
        assert payload["total_tools"] == 6
        assert payload["all_tools_passed"] is True
        assert payload["mutation_performed"] is False
        assert payload["data_contract"]
        urns.add(payload["asset_urn"])
    assert len(urns) == 7


def test_proof_galaxy_exposes_all_seven_cases_and_local_3d_engine():
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (root / "frontend" / "assets" / "app.js").read_text(encoding="utf-8")
    proof3d = (root / "frontend" / "assets" / "proof3d.js").read_text(encoding="utf-8")
    assert 'data-view="proof"' in html
    assert 'id="proof3d"' in html
    assert "/api/datahub/proof" in js
    assert "feature_quality" in proof3d
    assert "cancer_progression" in proof3d
    assert "model_drift" in proof3d
    assert "schema_mutation" in proof3d
    assert "biomarker_discordance" in proof3d
    assert "protein_conformation" in proof3d
    assert "microenvironment_escape" in proof3d
    assert "buildProteinWorld" in proof3d
    assert "buildMicroenvironmentWorld" in proof3d
    assert "mutation_performed" in (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")


def test_causal_observatory_binds_live_proof_to_spatial_topology():
    response = client.get("/api/datahub/observatory")
    assert response.status_code == 200
    payload = response.json()
    assert payload["truth_boundary"]["writes"] == 0
    assert payload["proof"]["total_tools"] == 6
    assert len(payload["topology"]["nodes"]) == 13
    assert len(payload["topology"]["edges"]) == 12
    assert payload["truth_boundary"]["catalog_coverage"] == "7/7 canonical DataHub assets"
    assert {item["id"] for item in payload["scenarios"]} == {
        "feature_quality", "cancer_progression", "model_drift", "schema_mutation",
        "biomarker_discordance", "protein_conformation", "microenvironment_escape",
    }
    root = Path(__file__).resolve().parents[2]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    engine = (root / "frontend" / "assets" / "observatory3d.js").read_text(encoding="utf-8")
    assert 'id="observatory3d"' in html
    assert "HUMAN POLICY MEMBRANE" in html
    assert "TubeGeometry" in engine
    assert "counterfactual" in (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")


def test_twin_scene_contract():
    response = client.get("/api/twin")
    assert response.status_code == 200
    payload = response.json()
    assert payload["research_only"] is True
    assert len(payload["stages"]) == 5
    assert payload["lesions"][-1]["appears_at"] == 4


def test_cohort_context_rail_contract():
    response = client.get("/api/cohorts")
    assert response.status_code == 200
    payload = response.json()
    assert [item["code"] for item in payload] == ["LUAD", "LIHC", "PAAD", "KIRC", "COAD", "SKCM", "GBM"]
    assert all(item["model"] and item["drivers"] and item["composition"] for item in payload)


def test_seven_rl_mission_cases_are_exposed():
    response = client.get("/api/missions/cases")
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == [
        "feature_quality",
        "cancer_progression",
        "model_drift",
        "schema_mutation",
        "biomarker_discordance",
        "protein_conformation",
        "microenvironment_escape",
    ]
    assert all(item["research_only"] is True for item in payload)
    assert all(item["datahub_native"] is True for item in payload)
    assert len({item["asset_name"] for item in payload}) == 7
    assert all(len(item["datahub_tools"]) == 6 for item in payload)
    assert next(item for item in payload if item["case_id"] == "protein_conformation")["state_arc"] == [
        "native-like", "intermediate", "provenance-rift"
    ]


def test_rl_mission_can_be_approved_and_replayed():
    started = client.post("/api/missions/start", json={"case_id": "feature_quality", "cohort": "LUAD"})
    assert started.status_code == 200
    mission_id = started.json()["mission_id"]

    import time
    payload = None
    for _ in range(40):
        payload = client.get(f"/api/missions/{mission_id}").json()
        if payload["status"] == "awaiting_approval":
            break
        time.sleep(0.02)
    assert payload["status"] == "awaiting_approval"
    rl = next(event for event in payload["events"] if event["type"] == "rl_decision")
    assert rl["rl"]["algorithm"] == "tabular-q-learning"
    assert rl["rl"]["action"] == "block_model"

    approved = client.post(
        f"/api/missions/{mission_id}/approve",
        json={"approval_secret": "change-me"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "completed"
    assert approved.json()["events"][-1]["decision"] == "UNBLOCK_MODEL"

    replay = client.get(f"/api/missions/{mission_id}/replay")
    assert replay.status_code == 200
    assert replay.json()["mode"] == "verified-replay"


def test_each_rl_case_selects_its_safety_action():
    expected = {
        "feature_quality": "block_model",
        "cancer_progression": "flag_research_review",
        "model_drift": "block_model",
        "schema_mutation": "block_consumers",
        "biomarker_discordance": "quarantine_biomarker",
        "protein_conformation": "freeze_structure_score",
        "microenvironment_escape": "flag_spatial_review",
    }
    for case_id, safe_action in expected.items():
        started = client.post("/api/missions/start", json={"case_id": case_id, "cohort": "LUAD"})
        assert started.status_code == 200
        decision = next(event for event in started.json()["events"] if event["type"] == "rl_decision")
        assert decision["rl"]["action"] == safe_action
        assert decision["rl"]["reward"] > 0


def test_incident_resolution_is_guarded_even_in_demo():
    denied = client.post(
        "/api/governance/resolve-incident",
        json={
            "incident_urn": "urn:li:incident:test",
            "asset_urn": "urn:li:dataset:(urn:li:dataPlatform:bigquery,oncotwin.progression_features,PROD)",
            "approval_secret": "wrong",
        },
    )
    assert denied.status_code == 403
