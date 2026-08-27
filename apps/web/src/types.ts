export type AgentName = 'Evidence Scout' | 'Nano Designer' | 'Twin Simulator' | 'Safety Steward'
export type CandidateId = 'A' | 'B' | 'C'

export type ArtifactTone = 'neutral' | 'good' | 'warning' | 'critical'

export interface ArtifactMetric {
  label: string
  value: string | number
  unit?: string | null
  tone: ArtifactTone
}

export interface AgentArtifact {
  kind: 'evidence_bundle' | 'candidate_blueprint' | 'distribution_comparison' | 'safety_decision' | 'approval_boundary'
  title: string
  detail: string
  metrics: ArtifactMetric[]
  confidence?: number | null
  evidence_ids: string[]
}

export interface ScenePatch {
  action: 'focus_clone' | 'spawn_candidates' | 'run_particle_paths' | 'reject_candidate' | 'show_approval_membrane'
  camera_target: 'clone_r7' | 'candidate_forge' | 'tumour_core' | 'liver_sink' | 'approval_boundary'
  overlay: 'clone_signal' | 'candidate_blueprints' | 'distribution_paths' | 'safety_quarantine' | 'approval_membrane'
  candidate_ids: CandidateId[]
  simulation_hour?: number | null
  emphasis: 'evidence' | 'design' | 'delivery' | 'risk' | 'authority'
}

export interface AgentEvent {
  sequence: number
  agent: AgentName
  status: 'working' | 'complete' | 'blocked'
  summary: string
  evidence_ids: string[]
  scene_action?: string
  tool_names?: string[]
  artifact?: AgentArtifact | null
  scene_patch?: ScenePatch | null
}

export type AdkTraceStatus = 'disabled' | 'queued' | 'running' | 'succeeded' | 'fallback'

export interface AdkTraceEvent {
  sequence: number
  author: string
  visible_agent: AgentName | null
  node_name: string | null
  event_type: string
  tool_names: string[]
  final_response: boolean
  phase: 'progress' | 'tool_call' | 'complete'
  scene_action?: string | null
  summary?: string | null
  artifact?: AgentArtifact | null
  scene_patch?: ScenePatch | null
}

export interface AdkMissionTrace {
  mission_id: string
  status: AdkTraceStatus
  workflow: string
  model: string
  events: AdkTraceEvent[]
  fallback_reason?: string | null
  model_call_executed: boolean
}

export interface CandidateResult {
  candidate: {
    id: CandidateId; name: string; particle_size_nm: number; surface_charge_mv: number
    ligand_affinity: number; stealth_score: number; release_half_life_hours: number; biodegradability: number
  }
  tumour_penetration: number
  tumour_payload_release: number
  liver_accumulation: number
  kidney_accumulation: number
  evidence_confidence: number
  safety_margin: number
  decision: 'preferred' | 'acceptable' | 'rejected'
  reason: string
}

export interface SimulationFrame {
  hour: number
  candidate_id: CandidateId
  tumour_penetration: number
  tumour_payload_release: number
  liver_accumulation: number
  kidney_accumulation: number
}

export interface Mission {
  id: string
  prompt: string
  state: 'running' | 'awaiting_human_approval' | 'approved' | 'failed'
  created_at: string
  events: AgentEvent[]
  receipt: {
    results: CandidateResult[]
    timeline?: SimulationFrame[]
    preferred_candidate_id: CandidateId
    rejected_candidate_ids: CandidateId[]
    receipt_sha256: string
    prior_memory_used?: string[]
    policy_version?: string
    evidence_ids?: string[]
  }
  approval_requested?: boolean
  approved_by?: string | null
}

export interface MemoryProof {
  configured_backend: string
  active_backend: string
  persistent: boolean
  healthy: boolean
  degraded: boolean
  mission_count: number
  approval_count: number
  latest_receipt_sha256_prefix: string | null
  resume_cursor_supported: boolean
}

export interface ApprovalResponse {
  approved: boolean
  mission_id: string
  approved_by: string
}

export interface ContextualExplanation {
  kind: 'contextual_explanation'
  accepted: boolean
  mission_id: string
  agent: 'Safety Steward'
  channel: 'text' | 'voice' | 'scene'
  question: string
  candidate_id: CandidateId
  decision: 'preferred' | 'acceptable' | 'rejected'
  explanation: string
  spoken_text: string
  focus_hour: number
  metrics: ArtifactMetric[]
  evidence_ids: string[]
  scene_patch: ScenePatch
  source_receipt_sha256_prefix: string
  approval_granted: false
}

export interface BoundedRerunPreview {
  kind: 'bounded_rerun'
  accepted: boolean
  parent_mission_id: string
  preview_id: string
  persisted: false
  lineage_status: 'preview_only'
  channel: 'text' | 'voice' | 'scene'
  command: string
  candidate_id: CandidateId
  change: {
    parameter: 'particle_size_nm'
    previous_value: number
    requested_value: number
    minimum: number
    maximum: number
    unit: 'nm'
  }
  before: CandidateResult
  after: CandidateResult
  results: CandidateResult[]
  timeline: SimulationFrame[]
  summary: string
  spoken_text: string
  focus_hour: number
  evidence_ids: string[]
  scene_patch: ScenePatch
  source_receipt_sha256_prefix: string
  preview_sha256: string
  approval_granted: false
}

export type MissionCommandResponse = ContextualExplanation | BoundedRerunPreview
