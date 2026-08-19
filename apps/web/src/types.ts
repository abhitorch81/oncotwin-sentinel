export type AgentName = 'Evidence Scout' | 'Nano Designer' | 'Twin Simulator' | 'Safety Steward'

export interface AgentEvent {
  sequence: number
  agent: AgentName
  status: 'working' | 'complete' | 'blocked'
  summary: string
  evidence_ids: string[]
  scene_action?: string
}

export interface CandidateResult {
  candidate: {
    id: string; name: string; particle_size_nm: number; surface_charge_mv: number
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

export interface Mission {
  id: string
  prompt: string
  state: 'running' | 'awaiting_human_approval' | 'approved' | 'failed'
  created_at: string
  events: AgentEvent[]
  receipt: {
    results: CandidateResult[]
    preferred_candidate_id: string
    rejected_candidate_ids: string[]
    receipt_sha256: string
  }
}

