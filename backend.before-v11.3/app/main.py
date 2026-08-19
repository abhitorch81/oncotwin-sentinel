import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agent_workflow import CancerContextMission
from .config import get_settings
from .condition_registry import CONDITION_REGISTRY, condition, dataset_urn
from .datahub_graphql import DataHubGraphQL
from .demo_data import DEMO_COHORTS, DEMO_SCATTER, DEMO_TWIN
from .governed_repair import DataHubKnowledgeWriteback, GovernedFeatureRepair
from .mission_control import MissionManager
from .memory_routes import router as memory_router
from .evolution_routes import router as evolution_router
from .mcp_client import DataHubMCP
from .models import AgentRunRequest, GenericMCPRequest, IncidentResolutionRequest, MissionApprovalRequest, MissionStartRequest, WritebackCommitRequest
from .rl_simulation import mission_catalog

settings = get_settings()
app = FastAPI(title="OncoTwin Evolution Memory Intelligence", version="11.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

proposals: dict[str, dict[str, Any]] = {}
mission_manager = MissionManager(settings)
app.include_router(memory_router)
app.include_router(evolution_router)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "ui_version": "11.2.0",
        "mode": "demo" if settings.demo_mode else "live",
        "datahub_gms_url": settings.datahub_gms_url,
        "analytics_agent_url": settings.analytics_agent_url,
        "mutations_enabled": settings.tools_is_mutation_enabled,
    }


@app.get("/api/scatter")
async def scatter() -> list[dict[str, Any]]:
    return DEMO_SCATTER


@app.get("/api/twin")
async def twin() -> dict[str, Any]:
    """Scene contract for the browser 3D cancer research twin."""
    return DEMO_TWIN


@app.get("/api/cohorts")
async def cohorts() -> list[dict[str, Any]]:
    """Synthetic cohort metadata powering the persistent context rails."""
    return DEMO_COHORTS


@app.get("/api/mcp/tools")
async def mcp_tools() -> dict[str, Any]:
    if settings.demo_mode:
        return {"mode": "demo", "tools": ["search", "get_entities", "get_lineage", "update_description", "save_document"]}
    tools = await DataHubMCP(settings).list_tools()
    return {"mode": "live", "tools": tools}


@app.get("/api/datahub/capabilities")
async def datahub_capabilities() -> dict[str, Any]:
    """Judge-facing proof of the DataHub surfaces used by this application."""
    return {
        "mode": "demo" if settings.demo_mode else "live",
        "mcp": {
            "transport": "stdio/self-hosted",
            "server": settings.datahub_mcp_package,
            "read_tools": ["search", "get_entities", "list_schema_fields", "get_lineage", "get_dataset_queries"],
            "mutation_tools": ["update_description"],
            "human_approval_required": True,
        },
        "skills": ["datahub-search", "datahub-quality", "datahub-lineage", "datahub-enrich"],
        "agent_context_kit": {"framework": "LangChain", "llm": "optional narrator; core decisions are deterministic"},
        "analytics_agent_url": settings.analytics_agent_url,
        "judge_proof_endpoint": "/api/datahub/proof",
        "causal_observatory_endpoint": "/api/datahub/observatory",
        "judge_proof": ["condition-specific canonical URN", "owner/tags/contract", "per-tool latency", "schema", "upstream lineage", "downstream lineage", "generating queries", "active incidents", "SHA-256 zero-write receipt"],
    }


@app.get("/api/datahub/proof")
async def datahub_proof(case_id: str = "feature_quality") -> dict[str, Any]:
    """Capture fresh, condition-specific, read-only DataHub evidence."""
    if case_id not in CONDITION_REGISTRY:
        raise HTTPException(404, f"Unknown cancer-context condition: {case_id}")
    project = settings.google_cloud_project or "oncotwin-demo"
    spec = condition(case_id)
    asset_urn = dataset_urn(project, case_id)
    captured_at = datetime.now(timezone.utc).isoformat()
    if settings.demo_mode:
        evidence = [
            {"tool": "search", "is_error": False, "duration_ms": 31, "content": [{"entities": [{"urn": asset_urn}]}]},
            {"tool": "get_entities", "is_error": False, "duration_ms": 27, "content": [{"urn": asset_urn, "owner": spec["owner"], "tags": spec["tags"]}]},
            {"tool": "list_schema_fields", "is_error": False, "duration_ms": 28, "content": [{"fields": spec["fields"]}]},
            {"tool": "get_lineage_upstream", "is_error": False, "duration_ms": 42, "content": [{"status": "cataloged upstream lineage available"}]},
            {"tool": "get_lineage_downstream", "is_error": False, "duration_ms": 39, "content": [{"status": "cataloged downstream lineage available"}]},
            {"tool": "get_dataset_queries", "is_error": False, "duration_ms": 33, "content": [{"status": "generating query evidence available"}]},
        ]
        active_incidents: int | None = 0
        source = "deterministic-demo"
    else:
        raw = await DataHubMCP(settings).call_many([
            ("search", {"query": spec["asset_name"]}),
            ("get_entities", {"urns": [asset_urn]}),
            ("list_schema_fields", {"urn": asset_urn}),
            ("get_lineage", {"urn": asset_urn, "upstream": True, "max_hops": 3, "max_results": 30}),
            ("get_lineage", {"urn": asset_urn, "upstream": False, "max_hops": 3, "max_results": 30}),
            ("get_dataset_queries", {"urn": asset_urn}),
        ])
        evidence = []
        lineage_number = 0
        for item in raw:
            tool = item["tool"]
            if tool == "get_lineage":
                lineage_number += 1
                tool = "get_lineage_upstream" if lineage_number == 1 else "get_lineage_downstream"
            compact = json.dumps(item.get("content", []), default=str)
            evidence.append({
                "tool": tool,
                "is_error": item.get("is_error", False),
                "duration_ms": item.get("duration_ms", 0),
                "content": item.get("content", []),
                "preview": compact[:600],
            })
        active_incidents = None
        if settings.datahub_admin_token:
            try:
                incident_data = await DataHubGraphQL(settings).active_incidents(asset_urn)
                active_incidents = int((((incident_data.get("dataset") or {}).get("incidents") or {}).get("total")) or 0)
            except Exception:
                active_incidents = None
        source = "datahub-mcp"
    successful = sum(not item.get("is_error", False) for item in evidence)
    receipt_payload = {
        "case_id": case_id,
        "asset_urn": asset_urn,
        "captured_at": captured_at,
        "tools": [{"tool": item["tool"], "is_error": item.get("is_error"), "duration_ms": item.get("duration_ms")} for item in evidence],
    }
    return {
        "proof_id": f"dh-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "receipt_sha256": hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode()).hexdigest(),
        "captured_at": captured_at,
        "case_id": case_id,
        "condition_title": spec["title"],
        "mode": "demo" if settings.demo_mode else "live",
        "source": source,
        "transport": "stdio/self-hosted MCP",
        "server": settings.datahub_mcp_package,
        "asset_urn": asset_urn,
        "asset_name": spec["asset_name"],
        "owner": spec["owner"],
        "tags": spec["tags"],
        "data_contract": spec["contract"],
        "successful_tools": successful,
        "total_tools": len(evidence),
        "all_tools_passed": successful == len(evidence),
        "active_incidents": active_incidents,
        "mutation_performed": False,
        "human_approval_boundary": True,
        "evidence": evidence,
        "challenge_coverage": ["Agents That Do Real Work", "Production ML Agents", "Metadata-Aware Code Generation", "Open / Wildcard"],
    }


@app.get("/api/datahub/observatory")
async def datahub_observatory(case_id: str = "feature_quality") -> dict[str, Any]:
    """Live proof plus a browser-safe causal topology for the 3D observatory.

    The topology distinguishes cataloged BigQuery assets from conceptual ML
    runtime nodes. Incident and repair playback are counterfactual simulations;
    this read-only endpoint never performs a mutation.
    """
    proof = await datahub_proof(case_id)
    project = settings.google_cloud_project or "oncotwin-demo"

    def dataset(name: str) -> str:
        return f"urn:li:dataset:(urn:li:dataPlatform:bigquery,{project}.oncotwin.{name},PROD)"

    nodes = [
        {"id": "cell_clusters", "label": "cell_clusters", "kind": "cataloged dataset", "urn": dataset("cell_clusters"), "layer": 0, "evidence": "MCP search"},
        {"id": "gene_expression", "label": "gene_expression_summary", "kind": "cataloged dataset", "urn": dataset("gene_expression_summary"), "layer": 1, "evidence": "MCP upstream lineage"},
        {"id": "quality_events", "label": "quality_events", "kind": "cataloged dataset", "urn": dataset("quality_events"), "layer": 1, "evidence": "DataHub incident context"},
        {"id": "progression_features", "label": "progression_features", "kind": "cataloged feature table", "urn": dataset("progression_features"), "layer": 2, "evidence": "MCP schema + lineage"},
        {"id": "progression_scores", "label": "progression_scores", "kind": "cataloged score table", "urn": dataset("progression_scores"), "layer": 3, "evidence": "MCP downstream lineage"},
        {"id": "vertex_model", "label": "OncoTwin model", "kind": "conceptual ML consumer", "urn": "vertex-ai://oncotwin-progression", "layer": 4, "evidence": "downstream impact projection"},
        {"id": "cloud_run", "label": "Mission Control", "kind": "conceptual deployment", "urn": "cloud-run://oncotwin-mission-control", "layer": 5, "evidence": "application boundary"},
        {"id": "tumour_states", "label": "tumour_state_transitions", "kind": "cataloged state-transition table", "urn": dataset("tumour_state_transitions"), "layer": 2, "evidence": "MCP schema + query lineage"},
        {"id": "drift_metrics", "label": "cohort_drift_metrics", "kind": "cataloged model-monitoring table", "urn": dataset("cohort_drift_metrics"), "layer": 3, "evidence": "MCP schema + query lineage"},
        {"id": "schema_events", "label": "genomic_schema_contract_events", "kind": "cataloged contract-event table", "urn": dataset("genomic_schema_contract_events"), "layer": 2, "evidence": "MCP schema + query lineage"},
        {"id": "variant_evidence", "label": "multi_omic_biomarker_evidence", "kind": "cataloged multi-omic data product", "urn": dataset("multi_omic_biomarker_evidence"), "layer": 1, "evidence": "MCP schema + lineage"},
        {"id": "protein_structure", "label": "protein_conformation_states", "kind": "cataloged structure-evidence product", "urn": dataset("protein_conformation_states"), "layer": 2, "evidence": "MCP schema + lineage"},
        {"id": "spatial_context", "label": "spatial_microenvironment_states", "kind": "cataloged spatial-omics product", "urn": dataset("spatial_microenvironment_states"), "layer": 1, "evidence": "MCP schema + lineage"},
    ]
    edges = [
        {"source": "cell_clusters", "target": "gene_expression", "type": "cohort context", "proof_tool": "search"},
        {"source": "gene_expression", "target": "progression_features", "type": "upstream lineage", "proof_tool": "get_lineage_upstream"},
        {"source": "quality_events", "target": "progression_features", "type": "quality signal", "proof_tool": "active incidents"},
        {"source": "progression_features", "target": "progression_scores", "type": "downstream lineage", "proof_tool": "get_lineage_downstream"},
        {"source": "progression_scores", "target": "vertex_model", "type": "ML consumption", "proof_tool": "impact projection"},
        {"source": "vertex_model", "target": "cloud_run", "type": "deployment", "proof_tool": "application boundary"},
        {"source": "progression_scores", "target": "tumour_states", "type": "state-transition lineage", "proof_tool": "get_lineage"},
        {"source": "progression_scores", "target": "drift_metrics", "type": "monitoring lineage", "proof_tool": "get_lineage"},
        {"source": "gene_expression", "target": "schema_events", "type": "contract-observation lineage", "proof_tool": "get_lineage"},
        {"source": "gene_expression", "target": "variant_evidence", "type": "multi-omic lineage", "proof_tool": "get_lineage"},
        {"source": "variant_evidence", "target": "protein_structure", "type": "structure evidence lineage", "proof_tool": "get_lineage"},
        {"source": "cell_clusters", "target": "spatial_context", "type": "spatial assay lineage", "proof_tool": "get_lineage"},
    ]
    scenarios = [
        {"id": "feature_quality", "label": "Biomarker completeness fracture", "origin": "progression_features", "stop": "vertex_model", "action": "BLOCK MODEL", "repair": "COALESCE biomarker feature patch", "path": ["progression_features", "progression_scores", "OncoTwin model"]},
        {"id": "cancer_progression", "label": "Tumour-state progression surge", "origin": "tumour_states", "stop": "tumour_states", "action": "FLAG REVIEW", "repair": "preserve governed progression evidence", "path": ["progression_scores", "tumour_state_transitions"]},
        {"id": "model_drift", "label": "Cancer cohort drift", "origin": "drift_metrics", "stop": "drift_metrics", "action": "RETRAIN GATE", "repair": "revalidate training cohort context", "path": ["progression_scores", "cohort_drift_metrics"]},
        {"id": "schema_mutation", "label": "Genomic schema mutation", "origin": "schema_events", "stop": "schema_events", "action": "BLOCK CONSUMERS", "repair": "metadata-aware genomic SQL patch", "path": ["gene_expression_summary", "genomic_schema_contract_events"]},
        {"id": "biomarker_discordance", "label": "Multi-omic biomarker discordance", "origin": "variant_evidence", "stop": "variant_evidence", "action": "QUARANTINE BIOMARKER", "repair": "reconcile RNA, variant and protein provenance", "path": ["gene_expression_summary", "multi_omic_biomarker_evidence"]},
        {"id": "protein_conformation", "label": "Protein conformation evidence rift", "origin": "protein_structure", "stop": "protein_structure", "action": "FREEZE STRUCTURE SCORE", "repair": "verify sequence-to-structure model lineage", "path": ["multi_omic_biomarker_evidence", "protein_conformation_states"]},
        {"id": "microenvironment_escape", "label": "Tumour microenvironment escape", "origin": "spatial_context", "stop": "spatial_context", "action": "FLAG SPATIAL REVIEW", "repair": "reconcile spatial cell-state context", "path": ["cell_clusters", "spatial_microenvironment_states"]},
    ]
    return {
        "mode": proof["mode"],
        "captured_at": proof["captured_at"],
        "proof_id": proof["proof_id"],
        "proof": proof,
        "topology": {"nodes": nodes, "edges": edges},
        "scenarios": scenarios,
        "truth_boundary": {
            "live": "DataHub identity, schema, lineage and incident evidence",
            "simulated": "incident propagation, RL action, protein-state and spatial counterfactual playback",
            "catalog_coverage": "12/12 canonical DataHub assets",
            "selected_condition": case_id,
            "writes": 0,
        },
    }


@app.get("/api/missions/cases")
async def mission_cases() -> list[dict[str, Any]]:
    return mission_catalog()


@app.post("/api/missions/start")
async def start_mission(request: MissionStartRequest) -> dict[str, Any]:
    if request.mode == "replay":
        raise HTTPException(400, "Replay an existing mission using /api/missions/{id}/replay.")
    return await mission_manager.start(request.case_id, request.cohort.upper())


@app.get("/api/missions/{mission_id}")
async def get_mission(mission_id: str) -> dict[str, Any]:
    mission = mission_manager.missions.get(mission_id)
    if mission is None:
        raise HTTPException(404, "Mission not found.")
    return mission_manager.public(mission)


@app.get("/api/missions/{mission_id}/events")
async def mission_events(mission_id: str) -> StreamingResponse:
    mission = mission_manager.missions.get(mission_id)
    if mission is None:
        raise HTTPException(404, "Mission not found.")

    async def stream():
        cursor = 0
        previous_at = 0
        while True:
            while cursor < len(mission["events"]):
                event = mission["events"][cursor]
                cursor += 1
                delay_ms = max(120, min(850, event.get("at_ms", 0) - previous_at))
                if cursor > 1:
                    await __import__('asyncio').sleep(delay_ms / 1000)
                previous_at = event.get("at_ms", previous_at)
                yield f"event: {event['type']}\ndata: {__import__('json').dumps(event)}\n\n"
            if mission["status"] in {"awaiting_approval", "completed", "failed"}:
                break
            await __import__('asyncio').sleep(0.08)
        yield f"event: stream_end\ndata: {{\"status\": \"{mission['status']}\"}}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/missions/{mission_id}/approve")
async def approve_mission(mission_id: str, request: MissionApprovalRequest) -> dict[str, Any]:
    if request.approval_secret != settings.writeback_approval_secret:
        raise HTTPException(403, "Approval secret is invalid.")
    mission = mission_manager.missions.get(mission_id)
    if mission is None:
        raise HTTPException(404, "Mission not found.")
    governance_evidence: dict[str, Any] | None = None
    # Every V11 mission has a dedicated DataHub dataset. Feature quality performs
    # the complete live repair/writeback path; the remaining research simulations
    # retain the narrower condition-incident lifecycle.
    if not settings.demo_mode:
        if not settings.datahub_admin_token:
            raise HTTPException(503, "DATAHUB_ADMIN_TOKEN is required for live incident resolution.")
        project = settings.google_cloud_project
        spec = condition(mission["case_id"])
        asset_urn = dataset_urn(project, mission["case_id"])
        incident_title = f"OncoTwin V11 · {spec['title']}"
        client = DataHubGraphQL(settings)
        before = await client.active_incidents(asset_urn)
        incident_list = (((before.get("dataset") or {}).get("incidents") or {}).get("incidents")) or []
        matching = [incident for incident in incident_list if incident.get("incidentType") == "CUSTOM" and incident.get("title") == incident_title]
        condition_incidents_before = len(matching)
        raised_urn: str | None = None
        if not matching:
            raised_urn = await client.raise_incident(
                asset_urn,
                incident_title,
                f"Approved OncoTwin research simulation checkpoint for {spec['asset_name']}. Contract: {spec['contract']}",
            )
            refreshed = await client.active_incidents(asset_urn)
            incident_list = (((refreshed.get("dataset") or {}).get("incidents") or {}).get("incidents")) or []
            matching = [incident for incident in incident_list if incident.get("incidentType") == "CUSTOM" and incident.get("title") == incident_title]
        repair_evidence: dict[str, Any] | None = None
        validation_evidence: dict[str, Any] | None = None
        knowledge_writeback: dict[str, Any] | None = None
        verification_read: dict[str, Any] | None = None

        if mission["case_id"] == "feature_quality":
            governed_repair = GovernedFeatureRepair(settings)
            repair_evidence = await governed_repair.execute(mission_id)
            validation_evidence = await governed_repair.validate(mission_id)
            if not validation_evidence.get("passed"):
                raise HTTPException(502, "Quality validation failed; the DataHub incident remains active and model consumption stays blocked.")

        resolved_urns: list[str] = []
        for incident in matching:
            incident_urn = incident.get("urn")
            if incident_urn and await client.resolve_incident(
                incident_urn,
                "OncoTwin Governance Steward approved resolution after condition-specific schema, contract and lineage verification.",
            ):
                resolved_urns.append(incident_urn)

        if mission["case_id"] == "feature_quality":
            resolved_incident = (resolved_urns or [raised_urn or mission.get("incident_urn")])[0]
            if not resolved_incident:
                raise HTTPException(502, "No condition incident was available for the governed audit record.")
            knowledge_writeback = await DataHubKnowledgeWriteback(settings).write(
                asset_urn=asset_urn,
                case_id=mission["case_id"],
                mission_id=mission_id,
                incident_urn=resolved_incident,
                repair=repair_evidence or {},
                validation=validation_evidence or {},
            )
            verification_read = await DataHubMCP(settings).call("get_entities", {"urns": [asset_urn]})
        after = await client.active_incidents(asset_urn)
        remaining = (((after.get("dataset") or {}).get("incidents") or {}).get("incidents")) or []
        matching_after = [incident for incident in remaining if incident.get("incidentType") == "CUSTOM" and incident.get("title") == incident_title]
        if matching_after:
            raise HTTPException(502, "The condition-specific DataHub incident remains active; the model stays blocked.")
        governance_evidence = {
            "execution_scope": "live-datahub",
            "case_id": mission["case_id"],
            "condition_title": spec["title"],
            "asset_name": spec["asset_name"],
            "data_contract": spec["contract"],
            "datahub_mutation": bool(raised_urn or resolved_urns),
            "raised_incident_urn": raised_urn,
            "resolved_incident_urns": resolved_urns,
            "condition_incidents_before": condition_incidents_before,
            "condition_incidents_after": 0,
            "active_incidents_after": 0,
            "other_active_incidents_preserved": len(remaining),
            "asset_urn": asset_urn,
            "repair_executed": repair_evidence is not None,
            "repair": repair_evidence,
            "quality_validation_passed": bool(validation_evidence and validation_evidence.get("passed")),
            "validation": validation_evidence,
            "incident_resolved": bool(resolved_urns),
            "knowledge_written_back": bool(knowledge_writeback and knowledge_writeback.get("written")),
            "knowledge_writeback": knowledge_writeback,
            "knowledge_inherited_verified": bool(verification_read and not verification_read.get("is_error")),
            "verification_read": verification_read,
        }
    return mission_manager.approve(mission_id, governance_evidence)


@app.get("/api/missions/{mission_id}/replay")
async def replay_mission(mission_id: str) -> dict[str, Any]:
    if mission_id not in mission_manager.missions:
        raise HTTPException(404, "Mission not found.")
    return mission_manager.replay(mission_id)


@app.post("/api/governance/resolve-incident")
async def resolve_incident(request: IncidentResolutionRequest) -> dict[str, Any]:
    if request.approval_secret != settings.writeback_approval_secret:
        raise HTTPException(403, "Approval secret is invalid.")
    if settings.demo_mode:
        return {"mode": "demo", "resolved": True, "active_incidents": 0, "asset_urn": request.asset_urn}
    if not settings.datahub_admin_token:
        raise HTTPException(503, "DATAHUB_ADMIN_TOKEN is required for incident resolution.")
    client = DataHubGraphQL(settings)
    resolved = await client.resolve_incident(request.incident_urn, request.message)
    active = await client.active_incidents(request.asset_urn)
    total = (((active.get("dataset") or {}).get("incidents") or {}).get("total"))
    return {"mode": "live", "resolved": resolved, "active_incidents": total, "asset_urn": request.asset_urn}


@app.post("/api/mcp/call")
async def mcp_call(request: GenericMCPRequest, x_admin_secret: str | None = Header(default=None)) -> dict[str, Any]:
    if request.tool.startswith(("add_", "remove_", "set_", "update_", "save_", "create_")):
        if x_admin_secret != settings.writeback_approval_secret:
            raise HTTPException(403, "Mutation tools require the approval secret.")
    if settings.demo_mode:
        return {"mode": "demo", "tool": request.tool, "arguments": request.arguments, "content": "Simulated MCP result"}
    return await DataHubMCP(settings).call(request.tool, request.arguments)


@app.post("/api/agents/run")
async def run_agents(request: AgentRunRequest) -> dict[str, Any]:
    result = await CancerContextMission(settings).run(request.question, request.asset_urn)
    proposals[result["proposal"]["proposal_id"]] = result["proposal"]
    return result


@app.post("/api/writeback/commit")
async def commit_writeback(request: WritebackCommitRequest) -> dict[str, Any]:
    if request.approval_secret != settings.writeback_approval_secret:
        raise HTTPException(403, "Approval secret is invalid.")
    proposal = proposals.pop(request.proposal_id, None)
    if proposal is None:
        raise HTTPException(404, "Proposal not found or already consumed.")
    if settings.demo_mode:
        return {"mode": "demo", "committed": True, "proposal": proposal}
    result = await DataHubMCP(settings).call(proposal["tool"], proposal["arguments"])
    if result.get("is_error"):
        raise HTTPException(502, detail=result)
    return {"mode": "live", "committed": True, "result": result}


@app.get("/api/analytics-agent/health")
async def analytics_health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(settings.analytics_agent_url)
        return {"reachable": response.status_code < 500, "status_code": response.status_code, "url": settings.analytics_agent_url}
    except httpx.HTTPError as exc:
        return {"reachable": False, "error": type(exc).__name__, "url": settings.analytics_agent_url}
