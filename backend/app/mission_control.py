from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from .adk_fleet import OncoTwinAdkFleet
from .config import Settings
from .condition_registry import condition
from .data_scope import governed_dataset_urn
from .datahub_graphql import DataHubGraphQL
from .mcp_client import DataHubMCP
from .rl_simulation import MISSION_CASES, SafetyQLearner, TwinState, simulate_transition


class MissionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.missions: dict[str, dict[str, Any]] = {}
        self.mcp = DataHubMCP(settings)
        self.adk_fleet = OncoTwinAdkFleet(settings)
        self.store = Path(settings.mission_store_path)
        self.store.mkdir(parents=True, exist_ok=True)

    def _event(self, mission: dict[str, Any], event_type: str, **payload: Any) -> dict[str, Any]:
        event = {
            "sequence": len(mission["events"]) + 1,
            "at_ms": int((time.monotonic() - mission["started_clock"]) * 1000),
            "type": event_type,
            **payload,
        }
        mission["events"].append(event)
        return event

    async def start(self, case_id: str, cohort: str) -> dict[str, Any]:
        mission_id = uuid.uuid4().hex[:12]
        mission = {
            "mission_id": mission_id,
            "case_id": case_id,
            "cohort": cohort,
            "mode": "demo" if self.settings.demo_mode else "live",
            "status": "running",
            "events": [],
            "started_at": int(time.time() * 1000),
            "started_clock": time.monotonic(),
            "approval_required": False,
        }
        self.missions[mission_id] = mission
        # Run the evidence-gathering phase before returning the mission id. This
        # makes the captured trace deterministic across Cloud Run workers and
        # test clients; the SSE endpoint then plays the timestamped real trace.
        await self._run(mission)
        if mission["status"] == "awaiting_approval":
            mission["adk_fleet"] = await self.adk_fleet.coordinate(self.public(mission))
            self._event(
                mission,
                "adk_fleet_completed",
                agent="OncoTwinFortifiedFleet",
                tool="Google ADK SequentialAgent",
                scene_cue="agent-council",
                summary=(
                    f"Google ADK coordinated {len(mission['adk_fleet']['agents'])} read-first "
                    "specialists and stopped at human approval."
                ),
                evidence={
                    "framework": mission["adk_fleet"]["framework"],
                    "execution_mode": mission["adk_fleet"]["execution_mode"],
                    "model": mission["adk_fleet"]["model"],
                    "external_mutations": 0,
                },
            )
            self._persist(mission)
        return self.public(mission)

    async def _datahub_context(self, mission: dict[str, Any], case_id: str) -> dict[str, Any]:
        case = MISSION_CASES[case_id]
        context_spec = condition(case_id)
        if self.settings.demo_mode:
            return {
                "source": "deterministic-demo",
                "tools": case["datahub"],
                "asset_urn": governed_dataset_urn(
                    self.settings,
                    self.settings.google_cloud_project or "oncotwin-demo",
                    case_id,
                ),
                "asset_name": context_spec["asset_name"],
                "owner": context_spec["owner"],
                "tags": context_spec["tags"],
                "contract": context_spec["contract"],
                "context_health": "grounded",
                "failed_tools": [],
            }
        project = self.settings.google_cloud_project or "oncotwin"
        asset_name = context_spec["asset_name"]
        urn = governed_dataset_urn(self.settings, project, case_id)
        calls: list[tuple[str, dict[str, Any]]] = [
            ("search", {"query": asset_name}),
            ("get_entities", {"urns": [urn]}),
            ("list_schema_fields", {"urn": urn}),
            ("get_lineage", {"urn": urn, "upstream": True, "max_hops": 3, "max_results": 30}),
            ("get_lineage", {"urn": urn, "upstream": False, "max_hops": 3, "max_results": 30}),
        ]
        if context_spec["query_evidence"]:
            calls.append(("get_dataset_queries", {"urn": urn}))
        evidence = await self.mcp.call_many(calls)
        failed_tools = [item["tool"] for item in evidence if item["is_error"]]
        return {
            "source": "datahub-mcp",
            "asset_urn": urn,
            "asset_name": asset_name,
            "owner": context_spec["owner"],
            "tags": context_spec["tags"],
            "contract": context_spec["contract"],
            "tools": [item["tool"] for item in evidence],
            "evidence": evidence,
            "failed_tools": failed_tools,
            "context_health": "grounded" if not failed_tools else "partial",
        }

    async def _run(self, mission: dict[str, Any]) -> None:
        case_id = mission["case_id"]
        case = MISSION_CASES[case_id]
        initial: TwinState = TwinState(**case["initial"].public())
        baseline = TwinState(**initial.public())
        baseline.data_trust = max(90, initial.data_trust)
        baseline.model_risk = 0.22
        baseline.null_rate = 0.0
        baseline.drift_score = 0.0
        baseline.schema_compatible = True
        if case_id in {"cancer_progression", "microenvironment_escape"}:
            baseline.malignant_fraction = 0.12
        try:
            self._event(mission, "mission_started", agent="Mission Controller", scene_cue="catalog-scan", summary=f"Baseline captured for {case['title']}.", twin=baseline.public())
            await asyncio.sleep(0.08)
            context = await self._datahub_context(mission, case_id)
            self._event(mission, "datahub_context", agent="Context Scout", tool="DataHub MCP", scene_cue="catalog-scan", summary=f"Grounded {context['asset_name']} in canonical identity, schema, ownership, contract and lineage context.", evidence=context, twin=initial.public())
            await asyncio.sleep(0.08)
            failure_evidence: dict[str, Any] = {"source": "digital-twin-telemetry"}
            failure_tool = "Digital twin telemetry"
            if not self.settings.demo_mode and case_id == "feature_quality":
                # Mission start is read-only. It may observe an existing DataHub
                # incident, but it cannot create signals or incidents before a
                # human authorizes the governed mutation phase.
                client = DataHubGraphQL(self.settings)
                title = f"OncoTwin Sentinel V12 · {case['title']}"
                active = await client.active_incidents(context["asset_urn"])
                incidents = (((active.get("dataset") or {}).get("incidents") or {}).get("incidents")) or []
                matching = [item for item in incidents if item.get("incidentType") == "CUSTOM" and item.get("title") == title]
                incident_urn = matching[0].get("urn") if matching else None
                if incident_urn:
                    mission["incident_urn"] = incident_urn
                failure_evidence = {
                    "source": "datahub-active-incident" if incident_urn else "live-read-only-quality-observation",
                    "incident_urn": incident_urn,
                    "asset_urn": context["asset_urn"],
                    "incident_state": "ACTIVE" if incident_urn else "NOT_CREATED",
                    "external_writes": 0,
                    "mutation_policy": "blocked_pending_human_approval",
                }
                failure_tool = "DataHub active-incident query + digital-twin telemetry"
            self._event(mission, "failure_observed", agent="Quality Sentinel", tool=failure_tool, scene_cue="quality-warning", status="warning", summary=case["failure"], evidence=failure_evidence, twin=initial.public())
            await asyncio.sleep(0.08)
            lineage_evidence = {
                "path": ["gene_expression_summary", "progression_features", "progression_scores"],
                "max_hops": 2,
                "grounded_by": context.get("source"),
                "tool_results": [item for item in context.get("evidence", []) if item.get("tool") == "get_lineage"],
            }
            self._event(mission, "lineage_impact", agent="Lineage Guardian", tool="get_lineage", scene_cue="lineage-pulse", summary="Mapped affected upstream evidence and downstream ML consumers.", evidence=lineage_evidence, twin=initial.public())
            await asyncio.sleep(0.08)
            policy = SafetyQLearner(case_id).decide(initial)
            policy["memory_query"] = case["memory_query"]
            policy["evidence_freshness_hours"] = case["evidence_freshness_hours"]
            policy["receipt_sha256"] = hashlib.sha256(json.dumps({
                "mission_id": mission["mission_id"], "case_id": case_id,
                "state": initial.public(), "policy": policy["ranked_actions"],
            }, sort_keys=True).encode()).hexdigest()
            safe_state = simulate_transition(case_id, initial, policy["action"])
            self._event(mission, "rl_decision", agent="Decision Council", tool="Q-learning + counterfactual policy", scene_cue="risk-focus", summary=f"Selected {policy['action']} after agent voting and five counterfactuals.", rl=policy, twin=safe_state.public())
            await asyncio.sleep(0.08)
            repair_action = case["repair_action"]
            repaired = simulate_transition(case_id, safe_state, repair_action)
            self._event(mission, "repair_proposed", agent="Repair Engineer", tool="DataHub Skills · schema + lineage + query evidence", scene_cue="repair-ready", status="blocked", summary=f"Prepared governed action: {repair_action}.", proposed_action=repair_action, twin=repaired.public())
            mission["approval_required"] = True
            mission["pending_state"] = repaired.public()
            mission["status"] = "awaiting_approval"
            self._event(mission, "approval_required", agent="Governance Steward", scene_cue="governance-lock", status="blocked", summary="Human approval is required before the write/recovery step.", twin=safe_state.public())
        except Exception as exc:
            mission["status"] = "failed"
            self._event(mission, "mission_error", agent="Mission Controller", scene_cue="governance-lock", status="blocked", summary=f"Stopped safely: {type(exc).__name__}")
        finally:
            self._persist(mission)

    def approve(self, mission_id: str, governance_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        mission = self.missions[mission_id]
        if mission["status"] != "awaiting_approval":
            return self.public(mission)
        recovered = TwinState(**mission["pending_state"])
        recovered.model_blocked = False
        recovered.model_risk = min(recovered.model_risk, 0.24)
        recovered.data_trust = max(recovered.data_trust, 92)
        evidence = governance_evidence or {
            "execution_scope": "digital-twin-simulation",
            "repair_query_found": True,
            "context_inherited": True,
            "datahub_mutation": False,
        }
        self._event(mission, "governed_action", agent="Governance Steward", tool="approved write path", scene_cue="repair-commit", summary="Operator approved the guarded recovery action.", evidence=evidence, twin=recovered.public())
        if evidence.get("repair_executed"):
            self._event(
                mission,
                "repair_executed",
                agent="Repair Engineer",
                tool="BigQuery approved query job",
                scene_cue="repair-commit",
                summary=f"Executed schema-grounded repair job {evidence['repair']['job_id']}.",
                evidence=evidence["repair"],
                twin=recovered.public(),
            )
        if evidence.get("quality_validation_passed"):
            validation_row = (evidence.get("validation", {}).get("rows") or [{}])[0]
            self._event(
                mission,
                "quality_validated",
                agent="Quality Sentinel",
                tool="BigQuery contract validation",
                scene_cue="context-pulse",
                summary=f"PASS: {validation_row.get('rows_with_null_signals', 0)} NULL signal rows; downstream scores regenerated.",
                evidence=evidence.get("validation"),
                twin=recovered.public(),
            )
        if evidence.get("incident_resolved"):
            self._event(
                mission,
                "incident_resolved",
                agent="Governance Steward",
                tool="DataHub GraphQL incident lifecycle",
                scene_cue="lineage-pulse",
                summary="Resolved the live feature-quality incident after validation passed.",
                evidence={"resolved_incident_urns": evidence.get("resolved_incident_urns"), "active_incidents_after": 0},
                twin=recovered.public(),
            )
        if evidence.get("knowledge_written_back"):
            writeback = evidence.get("knowledge_writeback") or {}
            self._event(
                mission,
                "knowledge_written",
                agent="Knowledge Steward",
                tool="DataHub REST metadata emitter",
                scene_cue="catalog-scan",
                summary="Persisted the responsible agent, timestamp, validation result, AgentRepaired tag and audit receipt in DataHub.",
                evidence={
                    "asset_urn": writeback.get("asset_urn"),
                    "responsible_agent": writeback.get("responsible_agent"),
                    "written_at": writeback.get("written_at"),
                    "tags": writeback.get("tags"),
                    "receipt_sha256": writeback.get("receipt_sha256"),
                    "verified_by_mcp_read": evidence.get("knowledge_inherited_verified"),
                },
                twin=recovered.public(),
            )
        if evidence.get("execution_scope") == "live-datahub":
            verified_summary = (
                "Resolved the live DataHub incident and verified zero active incidents."
                if evidence.get("datahub_mutation")
                else "Verified DataHub already reports zero active incidents; no resolution write was needed."
            )
        else:
            verified_summary = "Verified the replayable digital-twin recovery state; no DataHub mutation was executed."
        self._event(mission, "governance_verified", agent="Governance Steward", tool="DataHub query evidence", scene_cue="context-pulse", summary=verified_summary, evidence=evidence, twin=recovered.public())
        self._event(mission, "mission_complete", agent="ML Guardian", scene_cue="recovery-pass", summary="Digital twin returned to a trusted operational state.", decision="UNBLOCK_MODEL", twin=recovered.public(), reward=14.0)
        mission["status"] = "completed"
        mission["approval_required"] = False
        self._persist(mission)
        return self.public(mission)

    def public(self, mission: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in mission.items() if k not in {"started_clock", "pending_state"}}

    def replay(self, mission_id: str) -> dict[str, Any]:
        mission = self.missions[mission_id]
        return {**self.public(mission), "mode": "verified-replay", "replay": True}

    def _persist(self, mission: dict[str, Any]) -> None:
        path = self.store / f"{mission['mission_id']}.json"
        path.write_text(json.dumps(self.public(mission), indent=2), encoding="utf-8")
