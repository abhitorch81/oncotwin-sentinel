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


class SimulationFrame(BaseModel):
    hour: int = Field(ge=0, le=24)
    candidate_id: str
    tumour_penetration: float = Field(ge=0, le=1)
    tumour_payload_release: float = Field(ge=0, le=1)
    liver_accumulation: float = Field(ge=0, le=1)
    kidney_accumulation: float = Field(ge=0, le=1)


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
    timeline: list[SimulationFrame] = Field(default_factory=list)
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
    selected_candidate_id: Literal["A", "B", "C"] | None = None
    simulation_hour: int = Field(default=24, ge=0, le=24)


class ContextualExplanation(BaseModel):
    kind: Literal["contextual_explanation"] = "contextual_explanation"
    accepted: bool = True
    mission_id: str
    agent: Literal["Safety Steward"] = "Safety Steward"
    channel: Literal["text", "voice", "scene"]
    question: str
    candidate_id: Literal["A", "B", "C"]
    decision: Literal["preferred", "acceptable", "rejected"]
    explanation: str
    spoken_text: str
    focus_hour: int = Field(ge=0, le=24)
    metrics: list[ArtifactMetric]
    evidence_ids: list[str]
    scene_patch: ScenePatch
    source_receipt_sha256_prefix: str
    approval_granted: bool = False


class BoundedParameterChange(BaseModel):
    parameter: Literal["particle_size_nm"] = "particle_size_nm"
    previous_value: float
    requested_value: float
    minimum: float = 35
    maximum: float = 120
    unit: Literal["nm"] = "nm"


class BoundedRerunPreview(BaseModel):
    kind: Literal["bounded_rerun"] = "bounded_rerun"
    accepted: bool = True
    parent_mission_id: str
    preview_id: str
    persisted: bool = False
    lineage_status: Literal["preview_only"] = "preview_only"
    channel: Literal["text", "voice", "scene"]
    command: str
    candidate_id: Literal["A", "B", "C"]
    change: BoundedParameterChange
    before: SimulationResult
    after: SimulationResult
    results: list[SimulationResult]
    timeline: list[SimulationFrame]
    summary: str
    spoken_text: str
    focus_hour: int = 24
    evidence_ids: list[str]
    scene_patch: ScenePatch
    source_receipt_sha256_prefix: str
    preview_sha256: str
    approval_granted: bool = False


class ApprovalRequest(BaseModel):
    actor: str
    channel: Literal["ui", "voice", "api"] = "ui"
    confirmation: str
