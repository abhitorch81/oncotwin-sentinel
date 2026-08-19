"""Fail-safe command routing for voice, text and 3D selections.

This is intentionally the deterministic, low-latency lane. Gemini Live and ADK
can sit above this contract later; neither is falsely represented here.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from .agentic_models import AgenticCommandRequest, AgenticCommandResponse, AgenticSafetyEnvelope
from .mission_control import MissionManager
from .rl_simulation import MISSION_CASES


ANATOMY = ("lung", "liver", "kidney", "heart")
APPROVAL_WORDS = ("approve", "confirm", "authorize", "commit", "execute", "write back", "writeback")


def _contains(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _timepoint(text: str) -> int:
    if _contains(text, ("baseline", "first", "founder")):
        return 0
    if _contains(text, ("latest", "current", "last", "resistance")):
        return 3
    match = re.search(r"(?:timepoint|generation|stage)\s*(?:to|at|number)?\s*(\d+)", text)
    return max(0, min(3, int(match.group(1)))) if match else 3


def _anatomy(text: str) -> str:
    return next((item for item in ANATOMY if item in text), "lung")


def _base_response(request: AgenticCommandRequest, *, intent: str, spoken: str,
                   actions: list[dict[str, Any]], evidence: list[dict[str, Any]] | None = None,
                   confidence: float = .94, lane: str = "local_fast",
                   confirmation: bool = False, mission: dict[str, Any] | None = None) -> AgenticCommandResponse:
    return AgenticCommandResponse(
        command_id=uuid.uuid4().hex[:12],
        intent=intent,
        lane=lane,
        modality=request.modality,
        confidence=confidence,
        spoken_response=spoken,
        ui_actions=actions,
        evidence=evidence or [],
        safety=AgenticSafetyEnvelope(human_confirmation_required=confirmation),
        mission=mission,
    )


def build_agentic_router(mission_manager: MissionManager) -> APIRouter:
    router = APIRouter(tags=["agentic-multimodal"])

    @router.get("/api/agentic/capabilities")
    async def capabilities() -> dict[str, Any]:
        return {
            "edition": "agentic-multimodal",
            "lanes": {
                "local_fast": "Deterministic UI and Three.js commands",
                "investigation": "Read-first governed mission orchestration",
                "gemini_live": "planned integration; not active in this phase",
            },
            "intents": [
                "focus_clone", "focus_anatomy", "open_evidence", "set_timepoint",
                "compare_scenarios", "start_investigation", "request_approval",
            ],
            "signature_demo": "Show me why the resistant clone is red.",
            "safety": {
                "research_only": True,
                "clinical_action_allowed": False,
                "voice_approval_allowed": False,
                "external_mutations_from_command_router": False,
            },
        }

    @router.post("/api/agentic/commands", response_model=AgenticCommandResponse)
    async def route_command(request: AgenticCommandRequest) -> AgenticCommandResponse:
        text = " ".join(request.utterance.lower().split())

        # Approval language is checked first. The router may reveal the visible
        # human gate, but it never accepts a secret or performs the approval.
        if _contains(text, APPROVAL_WORDS):
            return _base_response(
                request,
                intent="request_approval",
                spoken="I opened the governed review gate. Voice cannot approve or execute a write; a human must inspect the evidence and confirm visibly.",
                actions=[{"type": "switch_view", "view": "mission"}, {"type": "open_approval_panel"}],
                evidence=[{"label": "Approval boundary", "value": "Visible human action required", "verified": True}],
                confidence=.99,
                confirmation=True,
            )

        if _contains(text, ("investigate", "investigation", "analyze", "analyse", "run mission", "start mission")):
            if request.case_id not in MISSION_CASES:
                raise HTTPException(status_code=422, detail="Unknown research mission case")
            mission = await mission_manager.start(request.case_id, request.cohort.upper())
            return _base_response(
                request,
                intent="start_investigation",
                lane="investigation",
                spoken=f"The governed {MISSION_CASES[request.case_id]['title']} investigation is ready for review. It stopped at the human approval boundary.",
                actions=[{"type": "switch_view", "view": "mission"}, {"type": "show_mission", "mission_id": mission["mission_id"]}],
                evidence=[{"label": "Mission status", "value": mission["status"], "verified": True}],
                confidence=.97,
                confirmation=bool(mission.get("approval_required")),
                mission=mission,
            )

        if _contains(text, ("compare", "counterfactual", "scenario", "alternative")):
            return _base_response(
                request,
                intent="compare_scenarios",
                spoken="I opened the uncertainty-aware clonal scenarios. They are research simulations, not individual outcome predictions.",
                actions=[{"type": "switch_view", "view": "evolution"}, {"type": "compare_scenarios"}],
                evidence=[{"label": "Truth boundary", "value": "Observed evidence remains separate from projected paths", "verified": True}],
            )

        if _contains(text, ("timepoint", "generation", "baseline", "latest", "stage")):
            generation = _timepoint(text)
            return _base_response(
                request,
                intent="set_timepoint",
                spoken=f"Showing clonal generation {generation}.",
                actions=[{"type": "switch_view", "view": "evolution"}, {"type": "set_timepoint", "generation": generation}],
            )

        if _contains(text, ANATOMY) or _contains(text, ("organ", "anatomy", "specimen")):
            organ = _anatomy(text)
            return _base_response(
                request,
                intent="focus_anatomy",
                spoken=f"Focusing the synthetic {organ} specimen in the 3D Decision Forge.",
                actions=[{"type": "switch_view", "view": "twin"}, {"type": "focus_anatomy", "anatomy": organ}],
            )

        if _contains(text, ("clone", "red", "resistant", "resistance", "met")):
            return _base_response(
                request,
                intent="focus_clone",
                spoken="The resistant clone is red because the renderer maps a risk score of 0.85 or higher to the high-risk color. I focused the highest-risk supported clone and opened its evidence; red is a research risk encoding, not a diagnosis.",
                actions=[
                    {"type": "switch_view", "view": "evolution"},
                    {"type": "focus_clone", "selector": "highest_risk", "prefer_label": "MET resistant"},
                    {"type": "open_evidence", "topic": "clone_color"},
                ],
                evidence=[
                    {"label": "3D color rule", "value": "risk_score >= 0.85 → red", "source": "Evolution renderer", "verified": True},
                    {"label": "Interpretation", "value": "Synthetic research risk encoding; not clinical significance", "source": "Safety policy", "verified": True},
                ],
                confidence=.99,
            )

        if _contains(text, ("evidence", "lineage", "why", "explain", "source", "provenance")):
            return _base_response(
                request,
                intent="open_evidence",
                spoken="I opened the evidence and lineage context. Unsupported claims remain visibly separated from verified evidence.",
                actions=[{"type": "open_evidence", "topic": "lineage"}],
                evidence=[{"label": "Evidence mode", "value": "Read-only lineage inspection", "verified": True}],
            )

        return _base_response(
            request,
            intent="open_evidence",
            spoken="I can focus a clone or organ, explain evidence, change generation, compare scenarios, or start a governed investigation.",
            actions=[{"type": "open_evidence", "topic": "help"}],
            confidence=.58,
        )

    return router
