import type { Mission } from '../types'

export const demoMission: Mission = {
  id: 'nano-demo-7f31',
  prompt: 'Investigate the resistant red clone and find a safer nanoparticle delivery strategy.',
  state: 'awaiting_human_approval',
  created_at: new Date().toISOString(),
  events: [
    { sequence: 1, agent: 'Evidence Scout', status: 'complete', summary: 'Grounded resistant red clone context and recovered a prior mission receipt.', evidence_ids: ['SYN-CLONE-R7'], scene_action: 'focus_clone' },
    { sequence: 2, agent: 'Nano Designer', status: 'complete', summary: 'Designed three bounded synthetic nanoparticle candidates.', evidence_ids: ['PARAM-ENVELOPE-V1'], scene_action: 'spawn_candidates' },
    { sequence: 3, agent: 'Twin Simulator', status: 'complete', summary: 'Compared tumour delivery against liver and kidney accumulation.', evidence_ids: ['SIM-MODEL-V1'], scene_action: 'run_particle_paths' },
    { sequence: 4, agent: 'Safety Steward', status: 'complete', summary: 'Rejected candidate B: off-target accumulation breached the synthetic safety envelope.', evidence_ids: ['POLICY-NANO-V1'], scene_action: 'reject_candidate' },
    { sequence: 5, agent: 'Safety Steward', status: 'blocked', summary: 'Evidence-complete. Paused at explicit human approval.', evidence_ids: ['APPROVAL-V1'], scene_action: 'show_approval_membrane' },
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

