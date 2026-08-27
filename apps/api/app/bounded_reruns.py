"""Bounded, non-persistent synthetic rerun previews derived from a mission receipt."""

from dataclasses import asdict, replace
import re

from .models import (
    BoundedParameterChange,
    BoundedRerunPreview,
    Candidate,
    Mission,
    ScenePatch,
    SimulationFrame,
    SimulationResult,
)
from .nano_simulator import NanoCandidate, NanoResult, build_timeline, receipt_digest, run_comparison


SIZE_BOUNDS_NM = (35.0, 120.0)
_SIZE_PATTERN = re.compile(r"(?P<size>\d+(?:\.\d+)?)\s*(?:nm|nanomet(?:er|re)s?)\b", re.IGNORECASE)


def is_bounded_rerun_command(command: str) -> bool:
    normalized = command.lower()
    return "rerun" in normalized and _SIZE_PATTERN.search(command) is not None


def _candidate_id(command: str, selected_candidate_id: str | None) -> str:
    if selected_candidate_id:
        return selected_candidate_id
    normalized = f" {command.upper().replace('-', ' ')} "
    for candidate_id in ("A", "B", "C"):
        if f" CANDIDATE {candidate_id} " in normalized:
            return candidate_id
    raise ValueError("Select candidate A, B, or C before requesting a rerun")


def _receipt_results(mission: Mission) -> list[NanoResult]:
    return [
        NanoResult(
            candidate=NanoCandidate(**result.candidate.model_dump()),
            tumour_penetration=result.tumour_penetration,
            tumour_payload_release=result.tumour_payload_release,
            liver_accumulation=result.liver_accumulation,
            kidney_accumulation=result.kidney_accumulation,
            evidence_confidence=result.evidence_confidence,
            safety_margin=result.safety_margin,
            decision=result.decision,
            reason=result.reason,
        )
        for result in mission.receipt.results
    ]


def _result_model(result: NanoResult) -> SimulationResult:
    return SimulationResult(
        candidate=Candidate(**asdict(result.candidate)),
        **{key: value for key, value in asdict(result).items() if key != "candidate"},
    )


def build_bounded_rerun_preview(
    mission: Mission,
    *,
    command: str,
    selected_candidate_id: str | None,
    channel: str,
) -> BoundedRerunPreview:
    if mission.receipt is None:
        raise ValueError("Mission receipt is unavailable")
    match = _SIZE_PATTERN.search(command)
    if match is None:
        raise ValueError("Specify a particle size in nanometres for the bounded rerun")

    requested_size = float(match.group("size"))
    minimum, maximum = SIZE_BOUNDS_NM
    if not minimum <= requested_size <= maximum:
        raise ValueError(f"Particle size must remain inside the {minimum:.0f}–{maximum:.0f} nm research envelope")

    candidate_id = _candidate_id(command, selected_candidate_id)
    receipt_results = _receipt_results(mission)
    before_raw = next((result for result in receipt_results if result.candidate.id == candidate_id), None)
    if before_raw is None:
        raise ValueError("Selected candidate is not present in this mission receipt")

    renamed = re.sub(r"-\d+(?:\.\d+)?$", f"-{requested_size:g}", before_raw.candidate.name)
    changed_candidate = replace(before_raw.candidate, name=renamed, particle_size_nm=requested_size)
    candidates = tuple(
        changed_candidate if result.candidate.id == candidate_id else result.candidate
        for result in receipt_results
    )
    rerun_raw = run_comparison(candidates)
    results = [_result_model(result) for result in rerun_raw]
    timeline = [SimulationFrame(**asdict(frame)) for frame in build_timeline(rerun_raw)]
    before = _result_model(before_raw)
    after = next(result for result in results if result.candidate.id == candidate_id)

    liver_delta = round((after.liver_accumulation - before.liver_accumulation) * 100)
    payload_delta = round((after.tumour_payload_release - before.tumour_payload_release) * 100)
    direction = "fell" if liver_delta < 0 else "rose" if liver_delta > 0 else "held"
    summary = (
        f"Bounded preview changed candidate {candidate_id} from {before.candidate.particle_size_nm:g} nm "
        f"to {requested_size:g} nm. Liver accumulation {direction} from "
        f"{round(before.liver_accumulation * 100)}% to {round(after.liver_accumulation * 100)}% "
        f"and tumour payload changed by {payload_delta:+d} points. The candidate remains "
        f"{after.decision}; this preview is not stored or approved."
    )
    digest_payload = {
        "parent_mission_id": mission.id,
        "candidate_id": candidate_id,
        "particle_size_nm": requested_size,
        "results": [result.model_dump() for result in results],
        "timeline": [frame.model_dump() for frame in timeline],
    }
    preview_sha256 = receipt_digest(digest_payload)
    scene_patch = ScenePatch(
        action="reject_candidate" if after.decision == "rejected" else "run_particle_paths",
        camera_target="liver_sink" if after.decision == "rejected" else "tumour_core",
        overlay="safety_quarantine" if after.decision == "rejected" else "distribution_paths",
        candidate_ids=[candidate_id],
        simulation_hour=24,
        emphasis="risk" if after.decision == "rejected" else "delivery",
    )
    return BoundedRerunPreview(
        parent_mission_id=mission.id,
        preview_id=f"preview-{preview_sha256[:12]}",
        channel=channel,
        command=command,
        candidate_id=candidate_id,
        change=BoundedParameterChange(
            previous_value=before.candidate.particle_size_nm,
            requested_value=requested_size,
        ),
        before=before,
        after=after,
        results=results,
        timeline=timeline,
        summary=summary,
        spoken_text=f"Twin Simulator. {summary} A human must authorize any persisted child run.",
        evidence_ids=["PARAM-ENVELOPE-V1", "SIM-MODEL-DETERMINISTIC-V1", "RERUN-PREVIEW-NOT-PERSISTED"],
        scene_patch=scene_patch,
        source_receipt_sha256_prefix=mission.receipt.receipt_sha256[:12],
        preview_sha256=preview_sha256,
    )
