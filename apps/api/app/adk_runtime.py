"""Non-blocking ADK runner and privacy-safe event translation."""

import asyncio
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from .agent_artifacts import event_contract_for_node
from .adk_fleet import VISIBLE_AGENTS, build_adk_fleet
from .models import AdkMissionTrace, AdkTraceEvent, Candidate, SimulationResult
from .nano_simulator import run_comparison


VISIBLE_BY_NODE = {item["name"]: item["visible_name"] for item in VISIBLE_AGENTS}
def _simulation_results() -> list[SimulationResult]:
    return [
        SimulationResult(
            candidate=Candidate(**asdict(result.candidate)),
            **{key: value for key, value in asdict(result).items() if key != "candidate"},
        )
        for result in run_comparison()
    ]


def _node_name(event: Any) -> str | None:
    direct = getattr(event, "node_name", None)
    if direct:
        return str(direct)
    info = getattr(event, "node_info", None)
    for attribute in ("name", "node_name"):
        value = getattr(info, attribute, None) if info else None
        if value:
            return str(value)
    author = getattr(event, "author", None)
    return str(author) if author in VISIBLE_BY_NODE else None


def _tool_names(event: Any) -> list[str]:
    """Extract tool identifiers only; never persist arguments or model reasoning."""
    names: list[str] = []
    getter = getattr(event, "get_function_calls", None)
    calls = getter() if callable(getter) else []
    for call in calls or []:
        name = getattr(call, "name", None)
        if name and str(name) not in names:
            names.append(str(name))
    return names


def translate_adk_event(event: Any, sequence: int, memory_count: int = 0) -> AdkTraceEvent:
    node = _node_name(event)
    final_check = getattr(event, "is_final_response", None)
    final_response = bool(final_check()) if callable(final_check) else False
    tool_names = _tool_names(event)
    contract = event_contract_for_node(
        node or "",
        _simulation_results(),
        memory_count=memory_count,
    )
    expose_contract = bool(contract and (tool_names or final_response))
    return AdkTraceEvent(
        sequence=sequence,
        author=str(getattr(event, "author", "adk_runtime")),
        visible_agent=VISIBLE_BY_NODE.get(node or ""),
        node_name=node,
        event_type=type(event).__name__,
        tool_names=tool_names,
        final_response=final_response,
        phase="complete" if final_response else "tool_call" if tool_names else "progress",
        scene_action=contract.scene_action if expose_contract else None,
        summary=contract.summary if expose_contract else None,
        artifact=contract.artifact if expose_contract else None,
        scene_patch=contract.scene_patch if expose_contract else None,
    )


class AdkTraceRepository:
    def __init__(self) -> None:
        self._traces: dict[str, AdkMissionTrace] = {}
        self._lock = asyncio.Lock()

    async def save(self, trace: AdkMissionTrace) -> None:
        async with self._lock:
            self._traces[trace.mission_id] = deepcopy(trace)

    async def get(self, mission_id: str) -> AdkMissionTrace | None:
        async with self._lock:
            trace = self._traces.get(mission_id)
            return deepcopy(trace) if trace else None


class AdkExecutionService:
    APP_NAME = "oncotwin-sentinel"
    USER_ID = "synthetic-research-demo"

    def __init__(self, repository: AdkTraceRepository) -> None:
        self.repository = repository

    async def prepare(self, mission_id: str, model: str, enabled: bool) -> AdkMissionTrace:
        trace = AdkMissionTrace(
            mission_id=mission_id,
            status="queued" if enabled else "disabled",
            model=model,
        )
        await self.repository.save(trace)
        return trace

    async def run(
        self,
        mission_id: str,
        prompt: str,
        model: str,
        memory_count: int = 0,
    ) -> None:
        """Execute at the integration boundary; failures activate deterministic fallback."""
        trace = AdkMissionTrace(mission_id=mission_id, status="running", model=model,
                                model_call_executed=True)
        await self.repository.save(trace)
        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            fleet = build_adk_fleet(model)
            sessions = InMemorySessionService()
            await sessions.create_session(
                app_name=self.APP_NAME,
                user_id=self.USER_ID,
                session_id=mission_id,
            )
            runner = Runner(agent=fleet, app_name=self.APP_NAME, session_service=sessions)
            message = types.Content(role="user", parts=[types.Part(text=prompt)])
            sequence = 0
            async for event in runner.run_async(
                user_id=self.USER_ID,
                session_id=mission_id,
                new_message=message,
            ):
                sequence += 1
                trace.events.append(
                    translate_adk_event(event, sequence, memory_count=memory_count)
                )
                await self.repository.save(trace)
            trace.status = "succeeded"
            await self.repository.save(trace)
        except Exception as exc:
            # This is the runner boundary, not a tool. Fail closed without leaking messages,
            # credentials, prompts, or stack traces into the user-facing mission contract.
            trace.status = "fallback"
            trace.fallback_reason = type(exc).__name__
            await self.repository.save(trace)
