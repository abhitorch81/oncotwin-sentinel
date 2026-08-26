import type { Mission } from '../types'

export const demoMission: Mission = {
  id: 'nano-demo-7f31',
  prompt: 'Investigate the resistant red clone and find a safer nanoparticle delivery strategy.',
  state: 'awaiting_human_approval',
  created_at: new Date().toISOString(),
  events: [
    { sequence: 1, agent: 'Evidence Scout', status: 'complete', summary: 'Isolated SYN-R7: persistence +31%, matrix resistance 72%; recovered 1 prior mission receipt.', evidence_ids: ['SYN-CLONE-R7', 'SYN-ASSAY-42'], scene_action: 'focus_clone',
      artifact: { kind: 'evidence_bundle', title: 'R7 synthetic evidence bundle', detail: 'The resistant clone is isolated with bounded phenotype signals and prior mission context.', confidence: .92, evidence_ids: ['SYN-CLONE-R7', 'SYN-ASSAY-42'], metrics: [{ label: 'Persistence', value: 31, unit: '%', tone: 'warning' }, { label: 'Matrix resistance', value: 72, unit: '%', tone: 'warning' }, { label: 'Prior receipts', value: 1, tone: 'neutral' }] },
      scene_patch: { action: 'focus_clone', camera_target: 'clone_r7', overlay: 'clone_signal', candidate_ids: [], emphasis: 'evidence' } },
    { sequence: 2, agent: 'Nano Designer', status: 'complete', summary: 'Forged A 48 nm/-8 mV, B 92 nm/+22 mV, and C 61 nm/-4 mV inside the bounded design envelope.', evidence_ids: ['PARAM-ENVELOPE-V1'], scene_action: 'spawn_candidates',
      artifact: { kind: 'candidate_blueprint', title: 'Three bounded nano blueprints', detail: 'Particle size, surface charge, ligand affinity, and release timing stay inside the synthetic envelope.', confidence: .96, evidence_ids: ['PARAM-ENVELOPE-V1'], metrics: [{ label: 'A · Aster', value: '48 nm / -8 mV', tone: 'neutral' }, { label: 'B · Brimstone', value: '92 nm / +22 mV', tone: 'warning' }, { label: 'C · Calyx', value: '61 nm / -4 mV', tone: 'good' }] },
      scene_patch: { action: 'spawn_candidates', camera_target: 'candidate_forge', overlay: 'candidate_blueprints', candidate_ids: ['A', 'B', 'C'], emphasis: 'design' } },
    { sequence: 3, agent: 'Twin Simulator', status: 'complete', summary: 'At 24 h, C delivered 91% payload with 14% liver/18% kidney accumulation; B reached 70% liver accumulation.', evidence_ids: ['SIM-MODEL-DETERMINISTIC-V1'], scene_action: 'run_particle_paths',
      artifact: { kind: 'distribution_comparison', title: '24-hour distribution comparison', detail: 'The deterministic twin compares tumour payload against liver and kidney accumulation.', confidence: .9, evidence_ids: ['SIM-MODEL-DETERMINISTIC-V1'], metrics: [{ label: 'C tumour payload', value: 91, unit: '%', tone: 'good' }, { label: 'C liver / kidney', value: '14 / 18', unit: '%', tone: 'good' }, { label: 'B liver accumulation', value: 70, unit: '%', tone: 'critical' }] },
      scene_patch: { action: 'run_particle_paths', camera_target: 'tumour_core', overlay: 'distribution_paths', candidate_ids: ['A', 'B', 'C'], simulation_hour: 24, emphasis: 'delivery' } },
    { sequence: 4, agent: 'Safety Steward', status: 'complete', summary: 'Rejected B: liver accumulation 70% exceeds the 45% policy ceiling; preserved C for human review.', evidence_ids: ['POLICY-NANO-SAFETY-V1'], scene_action: 'reject_candidate',
      artifact: { kind: 'safety_decision', title: 'B quarantined · C preferred', detail: 'Candidate B breaches the 45% synthetic liver ceiling. The steward preserves C but cannot approve it.', confidence: .84, evidence_ids: ['POLICY-NANO-SAFETY-V1'], metrics: [{ label: 'B liver', value: 70, unit: '%', tone: 'critical' }, { label: 'Policy ceiling', value: 45, unit: '%', tone: 'warning' }, { label: 'C safety margin', value: 73, unit: '%', tone: 'good' }] },
      scene_patch: { action: 'reject_candidate', camera_target: 'liver_sink', overlay: 'safety_quarantine', candidate_ids: ['B'], simulation_hour: 18, emphasis: 'risk' } },
    { sequence: 5, agent: 'Safety Steward', status: 'blocked', summary: 'Evidence complete. Autonomous execution is blocked at the explicit human authority boundary.', evidence_ids: ['APPROVAL-POLICY-V1'], scene_action: 'show_approval_membrane',
      artifact: { kind: 'approval_boundary', title: 'Human authority required', detail: 'Evidence is complete, but voice and agents remain unable to approve the research mission.', confidence: 1, evidence_ids: ['APPROVAL-POLICY-V1'], metrics: [{ label: 'Autonomous approval', value: 'BLOCKED', tone: 'critical' }] },
      scene_patch: { action: 'show_approval_membrane', camera_target: 'approval_boundary', overlay: 'approval_membrane', candidate_ids: [], emphasis: 'authority' } },
  ],
  receipt: {
    preferred_candidate_id: 'C', rejected_candidate_ids: ['B'], receipt_sha256: '93f7c9bb4cc8e2ac823116dd34ad2100f5f990ce9a1a94c5b17fe28c228ed79a',
    results: [
      { candidate: { id: 'A', name: 'Aster-48', particle_size_nm: 48, surface_charge_mv: -8, ligand_affinity: .72, stealth_score: .8, release_half_life_hours: 9, biodegradability: .77 }, tumour_penetration: .78, tumour_payload_release: .82, liver_accumulation: .20, kidney_accumulation: .24, evidence_confidence: .86, safety_margin: .58, decision: 'acceptable', reason: 'Within the synthetic safety envelope.' },
      { candidate: { id: 'B', name: 'Brimstone-92', particle_size_nm: 92, surface_charge_mv: 22, ligand_affinity: .88, stealth_score: .31, release_half_life_hours: 3, biodegradability: .38 }, tumour_penetration: .60, tumour_payload_release: .57, liver_accumulation: .70, kidney_accumulation: .38, evidence_confidence: .84, safety_margin: 0, decision: 'rejected', reason: 'Synthetic off-target accumulation exceeds the safety envelope.' },
      { candidate: { id: 'C', name: 'Calyx-61', particle_size_nm: 61, surface_charge_mv: -4, ligand_affinity: .91, stealth_score: .89, release_half_life_hours: 12, biodegradability: .86 }, tumour_penetration: .91, tumour_payload_release: .91, liver_accumulation: .14, kidney_accumulation: .18, evidence_confidence: .90, safety_margin: .73, decision: 'preferred', reason: 'Best delivery-to-risk balance.' },
    ],
  },
}
