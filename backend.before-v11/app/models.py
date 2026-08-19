from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    asset_urn: str | None = None


class TraceStep(BaseModel):
    agent: str
    tool: str
    scene_cue: str = "context-pulse"
    status: Literal["completed", "warning", "blocked"] = "completed"
    summary: str
    evidence: Any = None
    duration_ms: int = 0


class WritebackProposal(BaseModel):
    proposal_id: str
    tool: str
    asset_urn: str
    description: str
    arguments: dict[str, Any]
    requires_approval: bool = True


class WritebackCommitRequest(BaseModel):
    proposal_id: str
    approval_secret: str


class GenericMCPRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MissionStartRequest(BaseModel):
    case_id: Literal[
        "feature_quality", "cancer_progression", "model_drift", "schema_mutation",
        "biomarker_discordance", "protein_conformation", "microenvironment_escape",
    ] = "feature_quality"
    cohort: str = Field(default="LUAD", min_length=2, max_length=12)
    mode: Literal["live", "replay"] = "live"


class MissionApprovalRequest(BaseModel):
    approval_secret: str


class IncidentResolutionRequest(BaseModel):
    incident_urn: str = Field(min_length=10, max_length=500)
    asset_urn: str = Field(min_length=10, max_length=1000)
    approval_secret: str
    message: str = Field(
        default="OncoTwin Governance Steward approved resolution after repair evidence verification.",
        min_length=8,
        max_length=1000,
    )
