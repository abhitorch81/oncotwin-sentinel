from typing import Literal

from pydantic import BaseModel, Field


AgentName = Literal["Evidence Scout", "Nano Designer", "Twin Simulator", "Safety Steward"]
MissionState = Literal["running", "awaiting_human_approval", "approved", "failed"]
SceneAction = Literal[
    "focus_clone",
    "spawn_candidates",
    "run_particle_paths",
    "reject_candidate",
    "show_approval_membrane",
]
ArtifactKind = Literal[
    "evidence_bundle",
    "candidate_blueprint",
    "distribution_comparison",
    "safety_decision",
    "approval_boundary",
]


class Candidate(BaseModel):
    id: str
    name: str
    particle_size_nm: float
    surface_charge_mv: float
    ligand_affinity: float = Field(ge=0, le=1)
    stealth_score: float = Field(ge=0, le=1)
    release_half_life_hours: float
    biodegradability: float = Field(ge=0, le=1)


class SimulationResult(BaseModel):
    candidate: Candidate
    tumour_penetration: float
    tumour_payload_release: float
    liver_accumulation: float
    kidney_accumulation: float
    evidence_confidence: float
    safety_margin: float
    decision: Literal["preferred", "acceptable", "rejected"]
    reason: str


class ArtifactMetric(BaseModel):
    label: str
    value: str | int | float
    unit: str | None = None
    tone: Literal["neutral", "good", "warning", "critical"] = "neutral"


class AgentArtifact(BaseModel):
    kind: ArtifactKind
    title: str
    detail: str
    metrics: list[ArtifactMetric] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)


class ScenePatch(BaseModel):
    action: SceneAction
    camera_target: Literal[
        "clone_r7",
        "candidate_forge",
        "tumour_core",
        "liver_sink",
        "approval_boundary",
    ]
    overlay: Literal[
        "clone_signal",
        "candidate_blueprints",
        "distribution_paths",
        "safety_quarantine",
        "approval_membrane",
    ]
    candidate_ids: list[str] = Field(default_factory=list)
    simulation_hour: float | None = Field(default=None, ge=0, le=24)
    emphasis: Literal["evidence", "design", "delivery", "risk", "authority"]


class AgentEvent(BaseModel):
    sequence: int
    agent: AgentName
    status: Literal["working", "complete", "blocked"]
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    scene_action: str | None = None
    artifact: AgentArtifact | None = None
    scene_patch: ScenePatch | None = None


class MissionReceipt(BaseModel):
    mission_id: str
    created_at: str
    prompt: str
    synthetic_research_only: bool = True
    results: list[SimulationResult]
    preferred_candidate_id: str
    rejected_candidate_ids: list[str]
    evidence_ids: list[str]
    prior_memory_used: list[str]
    policy_version: str
    receipt_sha256: str


class Mission(BaseModel):
    id: str
    prompt: str
    state: MissionState
    created_at: str
    events: list[AgentEvent]
    receipt: MissionReceipt | None = None
    approval_requested: bool = False
    approved_by: str | None = None


class AdkTraceEvent(BaseModel):
    sequence: int
    author: str
    visible_agent: str | None = None
    node_name: str | None = None
    event_type: str
    tool_names: list[str] = Field(default_factory=list)
    final_response: bool = False
    phase: Literal["progress", "tool_call", "complete"] = "progress"
    scene_action: str | None = None
    summary: str | None = None
    artifact: AgentArtifact | None = None
    scene_patch: ScenePatch | None = None


class AdkMissionTrace(BaseModel):
    mission_id: str
    status: Literal["disabled", "queued", "running", "succeeded", "fallback"]
    workflow: str = "ADK2GraphWorkflow"
    model: str
    events: list[AdkTraceEvent] = Field(default_factory=list)
    fallback_reason: str | None = None
    model_call_executed: bool = False


class StartMissionRequest(BaseModel):
    prompt: str = "Investigate the resistant red clone and find a safer nanoparticle delivery strategy."


class CommandRequest(BaseModel):
    command: str
    channel: Literal["text", "voice", "scene"] = "text"


class ApprovalRequest(BaseModel):
    actor: str
    channel: Literal["ui", "voice", "api"] = "ui"
    confirmation: str
