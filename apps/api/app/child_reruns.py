"""Human-authorized persistence for bounded synthetic rerun previews."""

from datetime import datetime, timezone

from .agent_artifacts import (
    approval_boundary_event,
    designer_event,
    evidence_event,
    safety_event,
    simulator_event,
)
from .bounded_reruns import build_bounded_rerun_preview
from .memory import MissionRepository
from .models import (
    Mission,
    MissionLineage,
    MissionReceipt,
    PersistedChildRun,
    PersistRerunRequest,
)
from .nano_simulator import receipt_digest


PERSIST_CONFIRMATION = "PERSIST SYNTHETIC CHILD RUN"


def _validate_human_persistence(request: PersistRerunRequest) -> None:
    if request.channel != "ui":
        raise PermissionError("Voice and agents may preview reruns but cannot persist child missions")
    if request.confirmation != PERSIST_CONFIRMATION:
        raise PermissionError("Explicit UI confirmation is required to persist a child mission")


def persist_bounded_rerun_child(
    repository: MissionRepository,
    parent: Mission,
    request: PersistRerunRequest,
) -> PersistedChildRun:
    """Rebuild the preview server-side, verify it, and atomically store one child receipt."""
    _validate_human_persistence(request)
    if parent.receipt is None:
        raise ValueError("Parent mission receipt is unavailable")

    preview = build_bounded_rerun_preview(
        parent,
        command=f"Reduce candidate {request.candidate_id} to {request.requested_size_nm:g} nm and rerun",
        selected_candidate_id=request.candidate_id,
        channel="text",
    )
    if request.preview_id != preview.preview_id:
        raise ValueError("Preview identity does not match the server-verified rerun")

    child_id = f"nano-{preview.preview_sha256[:10]}"
    existing = repository.get(child_id)
    if existing:
        if not existing.lineage or existing.lineage.source_preview_id != preview.preview_id:
            raise ValueError("Child mission identifier conflicts with existing lineage")
        return PersistedChildRun(parent_mission_id=parent.id, child_mission=existing)

    now = datetime.now(timezone.utc).isoformat()
    root_id = parent.lineage.root_mission_id if parent.lineage else parent.id
    memories = list(dict.fromkeys([
        *(parent.receipt.prior_memory_used or []),
        parent.receipt.receipt_sha256[:12],
    ]))[-4:]
    rejected = [result.candidate.id for result in preview.results if result.decision == "rejected"]
    preferred = next(result.candidate.id for result in preview.results if result.decision == "preferred")
    prompt = (
        f"Persisted bounded child of {parent.id}: candidate {preview.candidate_id} "
        f"{preview.change.previous_value:g} nm to {preview.change.requested_value:g} nm."
    )
    lineage = MissionLineage(
        parent_mission_id=parent.id,
        root_mission_id=root_id,
        source_preview_id=preview.preview_id,
        source_preview_sha256=preview.preview_sha256,
        source_receipt_sha256=parent.receipt.receipt_sha256,
        candidate_id=preview.candidate_id,
        parameter_changes=[preview.change],
        persisted_by=request.actor,
    )
    evidence_ids = list(dict.fromkeys([
        *parent.receipt.evidence_ids,
        *preview.evidence_ids,
        "RERUN-CHILD-RECEIPT-V1",
        "HUMAN-PERSISTENCE-AUTHORITY-V1",
    ]))
    digest_payload = {
        "mission_id": child_id,
        "created_at": now,
        "prompt": prompt,
        "lineage": lineage.model_dump(),
        "results": [result.model_dump() for result in preview.results],
        "timeline": [frame.model_dump() for frame in preview.timeline],
        "preferred": preferred,
        "rejected": rejected,
        "memory": memories,
    }
    receipt = MissionReceipt(
        mission_id=child_id,
        created_at=now,
        prompt=prompt,
        results=preview.results,
        timeline=preview.timeline,
        preferred_candidate_id=preferred,
        rejected_candidate_ids=rejected,
        evidence_ids=evidence_ids,
        prior_memory_used=memories,
        policy_version=parent.receipt.policy_version,
        receipt_sha256=receipt_digest(digest_payload),
    )
    events = [
        evidence_event(1, len(memories)),
        designer_event(2, preview.results),
        simulator_event(3, preview.results),
        safety_event(4, preview.results),
        approval_boundary_event(5),
    ]
    child = Mission(
        id=child_id,
        prompt=prompt,
        state="awaiting_human_approval",
        created_at=now,
        events=events,
        receipt=receipt,
        lineage=lineage,
        approval_requested=False,
        approved_by=None,
    )
    repository.save(child)
    return PersistedChildRun(parent_mission_id=parent.id, child_mission=child)
