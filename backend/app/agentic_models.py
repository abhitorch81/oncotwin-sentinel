"""Contracts for the fast, deterministic multimodal command lane."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgenticCommandRequest(BaseModel):
    utterance: str = Field(min_length=2, max_length=1000)
    modality: Literal["voice", "text", "3d_selection", "event"] = "text"
    current_view: str = Field(default="mission", max_length=40)
    case_id: str = Field(default="feature_quality", max_length=80)
    cohort: str = Field(default="LUAD", max_length=32)
    selected_entity: dict[str, Any] | None = None


class AgenticSafetyEnvelope(BaseModel):
    research_only: bool = True
    clinical_action_allowed: bool = False
    voice_approval_allowed: bool = False
    external_mutation_performed: bool = False
    human_confirmation_required: bool = False


class AgenticCommandResponse(BaseModel):
    command_id: str
    intent: str
    lane: Literal["local_fast", "investigation"]
    modality: str
    confidence: float = Field(ge=0, le=1)
    spoken_response: str
    ui_actions: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    safety: AgenticSafetyEnvelope
    mission: dict[str, Any] | None = None
