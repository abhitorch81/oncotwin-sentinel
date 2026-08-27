from dataclasses import asdict
from datetime import datetime, timezone
import uuid

from .agent_artifacts import (
    approval_boundary_event,
    designer_event,
    evidence_event,
    safety_event,
    simulator_event,
)
from .memory import MissionRepository
from .models import Candidate, Mission, MissionReceipt, SimulationFrame, SimulationResult
from .nano_simulator import DEFAULT_CANDIDATES, build_timeline, receipt_digest, run_comparison


class MissionService:
    def __init__(self, repository: MissionRepository) -> None:
        self.repository = repository

    def start(self, prompt: str) -> Mission:
        mission_id = f"nano-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        memories = self.repository.relevant_receipts()
        raw_results = run_comparison(DEFAULT_CANDIDATES)
        results = [SimulationResult(candidate=Candidate(**asdict(r.candidate)), **{k: v for k, v in asdict(r).items() if k != "candidate"}) for r in raw_results]
        timeline = [SimulationFrame(**asdict(frame)) for frame in build_timeline(raw_results)]
        rejected = [r.candidate.id for r in results if r.decision == "rejected"]
        preferred = next(r.candidate.id for r in results if r.decision == "preferred")
        events = [
            evidence_event(1, len(memories)),
            designer_event(2),
            simulator_event(3, results),
            safety_event(4, results),
            approval_boundary_event(5),
        ]
        digest_payload = {"mission_id": mission_id, "created_at": now, "prompt": prompt,
                          "results": [r.model_dump() for r in results],
                          "timeline": [frame.model_dump() for frame in timeline], "preferred": preferred,
                          "rejected": rejected, "memory": memories}
        receipt = MissionReceipt(
            mission_id=mission_id, created_at=now, prompt=prompt, results=results, timeline=timeline,
            preferred_candidate_id=preferred, rejected_candidate_ids=rejected,
            evidence_ids=["SYN-CLONE-R7", "SYN-ASSAY-42", "PARAM-ENVELOPE-V1", "SIM-MODEL-DETERMINISTIC-V1"],
            prior_memory_used=memories, policy_version="nano-safety-v1",
            receipt_sha256=receipt_digest(digest_payload),
        )
        return self.repository.save(Mission(id=mission_id, prompt=prompt,
                                           state="awaiting_human_approval", created_at=now,
                                           events=events, receipt=receipt))
