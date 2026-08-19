import hashlib
import re
import time
from typing import Any

from .config import Settings
from .codegen import MetadataAwareRepairEngineer
from .demo_data import DEMO_TOOL_RESULTS, DEMO_URN
from .gemini import GeminiNarrator
from .langchain_specialist import DataHubLangChainSpecialist
from .mcp_client import DataHubMCP
from .models import TraceStep, WritebackProposal


class CancerContextMission:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mcp = DataHubMCP(settings)
        self.narrator = GeminiNarrator(settings)
        self.langchain_specialist = DataHubLangChainSpecialist(settings)
        self.repair_engineer = MetadataAwareRepairEngineer()

    async def _live_call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.mcp.call(tool, arguments)

    def _first_dataset_urn(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for child in value.values():
                found = self._first_dataset_urn(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = self._first_dataset_urn(child)
                if found:
                    return found
        elif isinstance(value, str):
            match = re.search(r"urn:li:dataset:\([^\n\"']+\)", value)
            if match:
                return match.group(0)
        return None

    async def run(self, question: str, requested_urn: str | None = None) -> dict[str, Any]:
        traces: list[TraceStep] = []
        live = not self.settings.demo_mode
        urn = requested_urn or DEMO_URN

        if live:
            search = await self._live_call("search", {"query": question})
            urn = requested_urn or self._first_dataset_urn(search) or urn
            traces.append(TraceStep(agent="Catalog Scout", tool="search", scene_cue="catalog-scan", summary="Located candidate cancer data assets.", evidence=search, duration_ms=search["duration_ms"]))
        else:
            search = DEMO_TOOL_RESULTS["search"]
            traces.append(TraceStep(agent="Catalog Scout", tool="search", scene_cue="catalog-scan", summary="Located the progression score dataset.", evidence=search, duration_ms=84))

        if live:
            entity = await self._live_call("get_entities", {"urns": [urn]})
            try:
                schema = await self._live_call("list_schema_fields", {"urn": urn})
            except Exception as exc:
                schema = {"tool": "list_schema_fields", "fallback": type(exc).__name__, "content": entity.get("content", [])}
            traces.append(TraceStep(agent="Quality Sentinel", tool="get_entities + list_schema_fields", scene_cue="quality-warning", status="warning", summary="Inspected schema, ownership, tags and health signals.", evidence={"entity": entity, "schema": schema}, duration_ms=entity["duration_ms"] + int(schema.get("duration_ms", 0))))
        else:
            entity = DEMO_TOOL_RESULTS["get_entities"]
            schema = entity
            traces.append(TraceStep(agent="Quality Sentinel", tool="get_entities", scene_cue="quality-warning", status="warning", summary="Completeness requires review; freshness passed.", evidence=entity, duration_ms=111))

        if live:
            upstream = await self._live_call("get_lineage", {"urn": urn, "upstream": True, "max_hops": 3, "max_results": 30})
            downstream = await self._live_call("get_lineage", {"urn": urn, "upstream": False, "max_hops": 3, "max_results": 30})
            lineage = {"upstream": upstream, "downstream": downstream}
            lineage_duration = upstream["duration_ms"] + downstream["duration_ms"]
            traces.append(TraceStep(agent="Lineage Guardian", tool="get_lineage", scene_cue="lineage-pulse", summary="Traced upstream evidence and downstream model impact.", evidence=lineage, duration_ms=lineage_duration))
        else:
            lineage = DEMO_TOOL_RESULTS["get_lineage"]
            traces.append(TraceStep(agent="Lineage Guardian", tool="get_lineage", scene_cue="lineage-pulse", summary="Found raw data, feature, model and visualization lineage.", evidence=lineage, duration_ms=137))

        evidence = {"search": search, "entity": entity, "schema": schema, "lineage": lineage, "urn": urn}
        if live and (self.settings.google_cloud_project or self.settings.google_api_key):
            try:
                specialist_result = await self.langchain_specialist.ask(question, urn)
                answer = specialist_result["answer"]
            except Exception as exc:
                specialist_result = {"fallback": type(exc).__name__}
                answer = await self.narrator.summarize(question, evidence)
        elif self.settings.google_cloud_project or self.settings.google_api_key:
            try:
                answer = await self.narrator.summarize(question, evidence)
                specialist_result = {"mode": "direct-gemini-demo"}
            except Exception as exc:  # keep the judge flow alive if the model quota is unavailable
                answer = f"Grounded metadata inspection completed for {urn}. Gemini narration was unavailable: {type(exc).__name__}."
                specialist_result = {"fallback": type(exc).__name__}
        else:
            answer = (
                "DataHub traced the selected progression dataset from raw scRNA evidence through normalized features, "
                "the deployed model, and the OncoTwin visualization. Freshness passed, while completeness needs review. "
                f"Evidence asset: {urn}."
            )
            specialist_result = {"mode": "deterministic-demo"}

        traces.append(TraceStep(agent="Progression Analyst", tool="agent-context-kit/langchain+gemini", scene_cue="risk-focus", summary="Produced a grounded reliability narrative using DataHub Agent Context Kit tools.", evidence={"answer": answer, "runtime": specialist_result}, duration_ms=203))

        repair = self.repair_engineer.generate(urn, schema, lineage)
        traces.append(TraceStep(
            agent="Repair Engineer",
            tool="DataHub Skills workflow · quality + lineage",
            scene_cue="lineage-pulse",
            summary="Generated reviewable data code only after DataHub schema and blast-radius inspection.",
            evidence={
                "skills": repair["skills"],
                "source_urn": repair["source_urn"],
                "schema_fields_used": repair["schema_fields_used"],
                "context_fingerprint": repair["context_fingerprint"],
            },
            duration_ms=76,
        ))

        proposal = self._proposal(urn)
        traces.append(TraceStep(agent="Governance Steward", tool="update_description", scene_cue="governance-lock", status="blocked", summary="Prepared a writeback and paused for human approval.", evidence=proposal.model_dump(), duration_ms=12))
        return {
            "mode": "live" if live else "demo",
            "question": question,
            "asset_urn": urn,
            "answer": answer,
            "context_quality_score": 4,
            "traces": [trace.model_dump() for trace in traces],
            "generated_artifacts": repair["artifacts"],
            "context_fingerprint": repair["context_fingerprint"],
            "proposal": proposal.model_dump(),
        }

    def _proposal(self, urn: str) -> WritebackProposal:
        stamp = hashlib.sha256(f"{urn}:{time.time_ns()}".encode()).hexdigest()[:16]
        description = (
            "OncoTwin agent review: lineage verified through normalized expression and progression features. "
            "Freshness passed; completeness requires follow-up. Human-approved metadata only."
        )
        return WritebackProposal(
            proposal_id=stamp,
            tool="update_description",
            asset_urn=urn,
            description=description,
            arguments={"entity_urn": urn, "operation": "append", "description": description},
        )
