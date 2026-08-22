from dataclasses import asdict
from datetime import datetime, timezone
import uuid

from .memory import MissionRepository
from .models import AgentEvent, Candidate, Mission, MissionReceipt, SimulationResult
from .nano_simulator import DEFAULT_CANDIDATES, receipt_digest, run_comparison


class MissionService:
    def __init__(self, repository: MissionRepository) -> None:
        self.repository = repository

    def start(self, prompt: str) -> Mission:
        mission_id = f"nano-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        memories = self.repository.relevant_receipts()
        events = [
            AgentEvent(sequence=1, agent="Evidence Scout", status="complete",
                       summary=f"Grounded resistant red clone context; retrieved {len(memories)} prior mission receipts.",
                       evidence_ids=["SYN-CLONE-R7", "SYN-ASSAY-42"], scene_action="focus_clone"),
            AgentEvent(sequence=2, agent="Nano Designer", status="complete",
                       summary="Designed three bounded synthetic nanoparticle candidates.",
                       evidence_ids=["PARAM-ENVELOPE-V1"], scene_action="spawn_candidates"),
            AgentEvent(sequence=3, agent="Twin Simulator", status="complete",
                       summary="Compared tumour penetration, release, and liver/kidney accumulation.",
                       evidence_ids=["SIM-MODEL-DETERMINISTIC-V1"], scene_action="run_particle_paths"),
        ]
        raw_results = run_comparison(DEFAULT_CANDIDATES)
        results = [SimulationResult(candidate=Candidate(**asdict(r.candidate)), **{k: v for k, v in asdict(r).items() if k != "candidate"}) for r in raw_results]
        rejected = [r.candidate.id for r in results if r.decision == "rejected"]
        preferred = next(r.candidate.id for r in results if r.decision == "preferred")
        events.extend([
            AgentEvent(sequence=4, agent="Safety Steward", status="complete",
                       summary=f"Rejected candidate {', '.join(rejected)} and blocked autonomous execution.",
                       evidence_ids=["POLICY-NANO-SAFETY-V1"], scene_action="reject_candidate"),
            AgentEvent(sequence=5, agent="Safety Steward", status="blocked",
                       summary="Mission is evidence-complete and paused at explicit human approval.",
                       evidence_ids=["APPROVAL-POLICY-V1"], scene_action="show_approval_membrane"),
        ])
        digest_payload = {"mission_id": mission_id, "created_at": now, "prompt": prompt,
                          "results": [r.model_dump() for r in results], "preferred": preferred,
                          "rejected": rejected, "memory": memories}
        receipt = MissionReceipt(
            mission_id=mission_id, created_at=now, prompt=prompt, results=results,
            preferred_candidate_id=preferred, rejected_candidate_ids=rejected,
            evidence_ids=["SYN-CLONE-R7", "SYN-ASSAY-42", "PARAM-ENVELOPE-V1", "SIM-MODEL-DETERMINISTIC-V1"],
            prior_memory_used=memories, policy_version="nano-safety-v1",
            receipt_sha256=receipt_digest(digest_payload),
        )
        return self.repository.save(Mission(id=mission_id, prompt=prompt,
                                           state="awaiting_human_approval", created_at=now,
                                           events=events, receipt=receipt))
