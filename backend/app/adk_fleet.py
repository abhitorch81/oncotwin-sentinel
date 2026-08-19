"""Google ADK specialist fleet with a fail-closed clinical/action boundary."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import uuid
from typing import Any

from fastapi import APIRouter
from google.genai import types

from .config import Settings


FLEET_AGENTS = (
    "EvidenceScout",
    "TwinAnalyst",
    "RepairPlanner",
    "SafetySteward",
)

AGENT_REGISTRY = (
    {"name": "EvidenceScout", "version": "12.2.0", "capability": "evidence-grounding", "tool_scope": "sanitized-read-only"},
    {"name": "TwinAnalyst", "version": "12.2.0", "capability": "digital-twin-interpretation", "tool_scope": "none"},
    {"name": "RepairPlanner", "version": "12.2.0", "capability": "reversible-repair-planning", "tool_scope": "proposal-only"},
    {"name": "SafetySteward", "version": "12.2.0", "capability": "policy-veto-and-escalation", "tool_scope": "none"},
)

FLEET_POLICY = {
    "research_only": True,
    "clinical_action_allowed": False,
    "external_mutation_allowed": False,
    "approval_secret_available": False,
    "human_confirmation_required": True,
}


def _adk_installed() -> bool:
    try:
        return importlib.util.find_spec("google.adk") is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def sanitized_mission_context(mission: dict[str, Any]) -> dict[str, Any]:
    """Expose only judge-safe facts to the model; never credentials or raw payloads."""
    return {
        "mission_id": str(mission.get("mission_id", ""))[:40],
        "case_id": str(mission.get("case_id", ""))[:80],
        "cohort": str(mission.get("cohort", ""))[:32],
        "status": str(mission.get("status", ""))[:40],
        "approval_required": bool(mission.get("approval_required", True)),
        "events": [
            {
                "type": str(event.get("type", ""))[:80],
                "agent": str(event.get("agent", ""))[:80],
                "summary": str(event.get("summary", ""))[:500],
                "status": str(event.get("status", ""))[:40],
            }
            for event in mission.get("events", [])[-16:]
        ],
        "policy": FLEET_POLICY,
    }


def adk_capabilities(settings: Settings) -> dict[str, Any]:
    installed = _adk_installed()
    credential_ready = bool(
        settings.google_cloud_project if settings.google_genai_use_vertexai else settings.google_api_key
    )
    if not settings.google_adk_enabled:
        status = "disabled"
    elif not settings.hackathon_model_compliant:
        status = "model_upgrade_required"
    elif not installed:
        status = "dependency_missing"
    elif settings.demo_mode or credential_ready:
        status = "ready"
    else:
        status = "configuration_required"
    return {
        "framework": "Google Agent Development Kit (ADK)",
        "status": status,
        "model": settings.gemini_model,
        "minimum_model": "Gemini 3.5 or newer",
        "model_compliant": settings.hackathon_model_compliant,
        "orchestration": "SequentialAgent",
        "agents": list(FLEET_AGENTS),
        "registry_endpoint": "/api/adk/registry",
        "observability": "timestamped MissionManager events + ADK author trace",
        "runtime": "Cloud Run",
        "state_authority": "MissionManager + persistent MemoryMesh",
        "policy": FLEET_POLICY,
    }


class OncoTwinAdkFleet:
    """Runs a read-only ADK reasoning pass over a governed mission trace."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _demo_result(self, context: dict[str, Any]) -> dict[str, Any]:
        trace = []
        descriptions = (
            "Inspected the governed evidence and provenance summary.",
            "Mapped evidence state to the synthetic 3D twin and uncertainty boundary.",
            "Prepared a reversible research repair proposal without executing it.",
            "Verified research-only scope and stopped at human approval.",
        )
        for sequence, (agent, summary) in enumerate(zip(FLEET_AGENTS, descriptions), 1):
            trace.append({"sequence": sequence, "agent": agent, "status": "completed", "summary": summary})
        return {
            "framework": "Google ADK",
            "orchestrator": "SequentialAgent",
            "execution_mode": "deterministic_demo",
            "model": self.settings.gemini_model,
            "session_id": f"demo-{context['mission_id']}",
            "agents": list(FLEET_AGENTS),
            "trace": trace,
            "final_summary": "ADK fleet recommends governed research review; no external mutation was executed.",
            "policy": FLEET_POLICY,
        }

    def _build_root_agent(self, context: dict[str, Any]) -> Any:
        # Lazy imports let the deterministic fallback remain available when a
        # local contributor has not installed the optional runtime yet.
        from google.adk.agents import LlmAgent, SequentialAgent

        def inspect_governed_mission() -> dict[str, Any]:
            """Return the sanitized read-only mission trace and safety policy."""
            return context

        evidence = LlmAgent(
            name="EvidenceScout",
            model=self.settings.gemini_model,
            description="Grounds the mission in supplied evidence and provenance.",
            instruction=(
                "Call inspect_governed_mission. Summarize only supplied evidence. "
                "Do not infer diagnosis, treatment, patient outcome, or missing facts."
            ),
            tools=[inspect_governed_mission],
            output_key="evidence_assessment",
        )
        twin = LlmAgent(
            name="TwinAnalyst",
            model=self.settings.gemini_model,
            description="Maps evidence to the synthetic digital twin.",
            instruction=(
                "Using {evidence_assessment}, explain the synthetic twin state and uncertainty. "
                "This is research simulation, never clinical interpretation."
            ),
            output_key="twin_assessment",
        )
        repair = LlmAgent(
            name="RepairPlanner",
            model=self.settings.gemini_model,
            description="Proposes reversible data or model workflow repairs.",
            instruction=(
                "Using {evidence_assessment} and {twin_assessment}, propose one reversible "
                "research workflow repair. Never execute tools or claim a write occurred."
            ),
            output_key="repair_proposal",
        )
        safety = LlmAgent(
            name="SafetySteward",
            model=self.settings.gemini_model,
            description="Applies the human approval and medical-use boundary.",
            instruction=(
                "Review {repair_proposal}. State uncertainties and conclude that external "
                "mutation requires visible human approval. Never diagnose or recommend treatment."
            ),
            output_key="safety_verdict",
        )
        return SequentialAgent(
            name="OncoTwinFortifiedFleet",
            description="Google ADK research-agent fleet with a fail-closed approval boundary.",
            sub_agents=[evidence, twin, repair, safety],
        )

    async def _run_live(self, context: dict[str, Any]) -> dict[str, Any]:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        session_id = uuid.uuid4().hex
        user_id = f"research-{context['cohort'].lower()}"
        session_service = InMemorySessionService()
        await session_service.create_session(
            app_name=self.settings.google_adk_app_name,
            user_id=user_id,
            session_id=session_id,
        )
        runner = Runner(
            agent=self._build_root_agent(context),
            app_name=self.settings.google_adk_app_name,
            session_service=session_service,
        )
        prompt = (
            "Coordinate the governed OncoTwin mission below. Use only the read-only tool, "
            "keep observed evidence separate from projections, and stop at human approval.\n"
            + json.dumps(context, sort_keys=True)
        )
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        trace: list[dict[str, Any]] = []
        final_summary = "ADK fleet completed without a textual verdict."
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            author = str(getattr(event, "author", "OncoTwinFortifiedFleet"))[:80]
            content = getattr(event, "content", None)
            text = " ".join(
                str(getattr(part, "text", "")).strip()
                for part in (getattr(content, "parts", None) or [])
                if getattr(part, "text", None)
            ).strip()
            if author in FLEET_AGENTS and text:
                trace.append({
                    "sequence": len(trace) + 1,
                    "agent": author,
                    "status": "completed",
                    "summary": text[:700],
                })
                final_summary = text[:1200]
        return {
            "framework": "Google ADK",
            "orchestrator": "SequentialAgent",
            "execution_mode": "google_adk_runtime",
            "model": self.settings.gemini_model,
            "session_id": session_id,
            "agents": list(FLEET_AGENTS),
            "trace": trace,
            "final_summary": final_summary,
            "policy": FLEET_POLICY,
        }

    async def coordinate(self, mission: dict[str, Any]) -> dict[str, Any]:
        context = sanitized_mission_context(mission)
        if self.settings.demo_mode:
            return self._demo_result(context)
        capabilities = adk_capabilities(self.settings)
        if capabilities["status"] != "ready":
            return {
                "framework": "Google ADK",
                "orchestrator": "SequentialAgent",
                "execution_mode": "safe_fallback",
                "model": self.settings.gemini_model,
                "agents": list(FLEET_AGENTS),
                "trace": [],
                "final_summary": f"ADK did not run: {capabilities['status']}.",
                "policy": FLEET_POLICY,
            }
        try:
            async with asyncio.timeout(self.settings.google_adk_timeout_seconds):
                return await self._run_live(context)
        except Exception as exc:
            return {
                "framework": "Google ADK",
                "orchestrator": "SequentialAgent",
                "execution_mode": "safe_fallback",
                "model": self.settings.gemini_model,
                "agents": list(FLEET_AGENTS),
                "trace": [],
                "final_summary": f"ADK stopped safely: {type(exc).__name__}.",
                "policy": FLEET_POLICY,
            }


def build_adk_router(settings: Settings, fleet: OncoTwinAdkFleet) -> APIRouter:
    router = APIRouter(tags=["google-adk"])

    @router.get("/api/adk/capabilities")
    async def capabilities() -> dict[str, Any]:
        return adk_capabilities(settings)

    @router.get("/api/adk/registry")
    async def registry() -> dict[str, Any]:
        return {
            "registry": "OncoTwin enterprise agent catalog",
            "framework": "Google ADK",
            "agents": list(AGENT_REGISTRY),
            "lifecycle": {"versioned": True, "runtime": "Cloud Run", "mutation_default": "deny"},
        }

    return router
