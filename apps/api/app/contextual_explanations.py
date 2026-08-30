"""Receipt-grounded candidate explanations shared by text and future Gemini Live voice."""

from dataclasses import asdict

from .models import (
    ArtifactMetric,
    ContextualExplanation,
    Mission,
    SimulationFrame,
    ScenePatch,
)
from .nano_simulator import NanoCandidate, NanoResult, build_timeline


def _percent(value: float) -> int:
    return round(value * 100)


def _candidate_from_question(question: str) -> str | None:
    normalized = f" {question.upper().replace('-', ' ')} "
    for candidate_id in ("A", "B", "C"):
        if f" CANDIDATE {candidate_id} " in normalized:
            return candidate_id
    return None


def _receipt_timeline(mission: Mission) -> tuple[list[SimulationFrame], bool]:
    """Return stored frames, or reconstruct identical kinetics for legacy receipts."""
    if mission.receipt.timeline:
        return mission.receipt.timeline, False

    raw_results = [
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
    return [SimulationFrame(**asdict(frame)) for frame in build_timeline(raw_results)], True


def build_contextual_explanation(
    mission: Mission,
    *,
    question: str,
    selected_candidate_id: str | None,
    simulation_hour: int,
    channel: str,
    image_evidence: dict | None = None,
) -> ContextualExplanation:
    """Explain a decision using only the selected mission receipt and policy evidence."""
    if mission.receipt is None:
        raise ValueError("Mission receipt is unavailable")

    candidate_id = selected_candidate_id or _candidate_from_question(question)
    if candidate_id is None:
        raise ValueError("Select candidate A, B, or C before asking for an explanation")

    result = next(
        (item for item in mission.receipt.results if item.candidate.id == candidate_id),
        None,
    )
    if result is None:
        raise ValueError("Selected candidate is not present in this mission receipt")

    receipt_timeline, timeline_reconstructed = _receipt_timeline(mission)
    frames = sorted(
        (
            frame for frame in receipt_timeline
            if frame.candidate_id == candidate_id
        ),
        key=lambda frame: frame.hour,
    )
    current = next((frame for frame in frames if frame.hour == simulation_hour), None)
    if current is None:
        raise ValueError("Selected simulation hour is not present in this mission receipt")

    evidence_ids = ["POLICY-NANO-SAFETY-V1", "SIM-MODEL-DETERMINISTIC-V1"]
    if timeline_reconstructed:
        evidence_ids.append("LEGACY-RECEIPT-TIMELINE-RECONSTRUCTED-V1")
    if result.decision == "rejected":
        threshold = .45
        breach = next((frame for frame in frames if frame.liver_accumulation > threshold), current)
        final = frames[-1]
        focus_hour = breach.hour
        explanation = (
            f"{result.candidate.name} was rejected because its liver accumulation crossed "
            f"the {_percent(threshold)}% synthetic policy ceiling at T+{breach.hour}H "
            f"({_percent(breach.liver_accumulation)}%) and reached "
            f"{_percent(final.liver_accumulation)}% by T+{final.hour}H. "
            "The Safety Steward quarantined it and preserved candidate C for human review."
        )
        metrics = [
            ArtifactMetric(label=f"Liver · T+{breach.hour}H", value=_percent(breach.liver_accumulation), unit="%", tone="critical"),
            ArtifactMetric(label="Policy ceiling", value=_percent(threshold), unit="%", tone="warning"),
            ArtifactMetric(label=f"Liver · T+{final.hour}H", value=_percent(final.liver_accumulation), unit="%", tone="critical"),
        ]
        patch = ScenePatch(
            action="reject_candidate",
            camera_target="liver_sink",
            overlay="safety_quarantine",
            candidate_ids=[candidate_id],
            simulation_hour=focus_hour,
            emphasis="risk",
        )
    else:
        focus_hour = simulation_hour
        explanation = (
            f"{result.candidate.name} is {result.decision} at T+{simulation_hour}H: "
            f"tumour payload is {_percent(current.tumour_payload_release)}%, while liver "
            f"and kidney accumulation are {_percent(current.liver_accumulation)}% and "
            f"{_percent(current.kidney_accumulation)}%. {result.reason}"
        )
        metrics = [
            ArtifactMetric(label=f"Tumour · T+{simulation_hour}H", value=_percent(current.tumour_payload_release), unit="%", tone="good"),
            ArtifactMetric(label=f"Liver · T+{simulation_hour}H", value=_percent(current.liver_accumulation), unit="%", tone="neutral"),
            ArtifactMetric(label=f"Kidney · T+{simulation_hour}H", value=_percent(current.kidney_accumulation), unit="%", tone="neutral"),
        ]
        patch = ScenePatch(
            action="run_particle_paths",
            camera_target="tumour_core",
            overlay="distribution_paths",
            candidate_ids=[candidate_id],
            simulation_hour=focus_hour,
            emphasis="delivery",
        )

    image_evidence_id = None
    if image_evidence:
        image_evidence_id = image_evidence.get("evidence_id")
        if image_evidence.get("mission_id") != mission.id:
            raise ValueError("Image evidence does not belong to this mission")
        image_candidate = image_evidence.get("selected_candidate_id")
        if image_candidate and image_candidate != candidate_id:
            raise ValueError("Image evidence is bound to a different candidate")
        similarity = _percent(float(image_evidence.get("r7_similarity", 0)))
        matrix_signal = _percent(float(image_evidence.get("matrix_resistance_signal", 0)))
        confidence = _percent(float(image_evidence.get("confidence", 0)))
        pattern = str(image_evidence.get("synthetic_pattern", "unknown")).replace("_", " ")
        explanation += (
            f" Image evidence {image_evidence_id} adds a {pattern} synthetic pattern with "
            f"{similarity}% R7 similarity and {matrix_signal}% matrix-resistance signal. "
            "It provides bounded supporting context but does not alter the stored simulation receipt or approval boundary."
        )
        metrics.append(ArtifactMetric(label="Image confidence", value=confidence, unit="%", tone="neutral"))
        evidence_ids.append(image_evidence_id)
    spoken_text = f"Safety Steward. {explanation} Approval still requires a human."
    return ContextualExplanation(
        mission_id=mission.id,
        channel=channel,
        question=question,
        candidate_id=candidate_id,
        decision=result.decision,
        explanation=explanation,
        spoken_text=spoken_text,
        focus_hour=focus_hour,
        metrics=metrics,
        evidence_ids=evidence_ids,
        scene_patch=patch,
        source_receipt_sha256_prefix=mission.receipt.receipt_sha256[:12],
        image_evidence_id=image_evidence_id,
    )
