"""Deterministic, inspectable work products shared by fallback and live ADK traces."""

from .models import AgentArtifact, AgentEvent, ArtifactMetric, ScenePatch, SimulationResult


def _percent(value: float) -> int:
    return round(value * 100)


def evidence_event(sequence: int, memory_count: int) -> AgentEvent:
    evidence_ids = ["SYN-CLONE-R7", "SYN-ASSAY-42"]
    artifact = AgentArtifact(
        kind="evidence_bundle",
        title="R7 synthetic evidence bundle",
        detail="The resistant clone is isolated with bounded phenotype signals and prior mission context.",
        metrics=[
            ArtifactMetric(label="Persistence", value=31, unit="%", tone="warning"),
            ArtifactMetric(label="Matrix resistance", value=72, unit="%", tone="warning"),
            ArtifactMetric(label="Prior receipts", value=memory_count, tone="neutral"),
        ],
        confidence=.92,
        evidence_ids=evidence_ids,
    )
    patch = ScenePatch(
        action="focus_clone",
        camera_target="clone_r7",
        overlay="clone_signal",
        emphasis="evidence",
    )
    return AgentEvent(
        sequence=sequence,
        agent="Evidence Scout",
        status="complete",
        summary=(
            f"Isolated SYN-R7: persistence +31%, matrix resistance 72%; "
            f"recovered {memory_count} prior mission receipts."
        ),
        evidence_ids=evidence_ids,
        scene_action=patch.action,
        artifact=artifact,
        scene_patch=patch,
    )


def designer_event(sequence: int) -> AgentEvent:
    artifact = AgentArtifact(
        kind="candidate_blueprint",
        title="Three bounded nano blueprints",
        detail="Particle size, surface charge, ligand affinity, and release timing stay inside the synthetic envelope.",
        metrics=[
            ArtifactMetric(label="A · Aster", value="48 nm / -8 mV", tone="neutral"),
            ArtifactMetric(label="B · Brimstone", value="92 nm / +22 mV", tone="warning"),
            ArtifactMetric(label="C · Calyx", value="61 nm / -4 mV", tone="good"),
        ],
        confidence=.96,
        evidence_ids=["PARAM-ENVELOPE-V1"],
    )
    patch = ScenePatch(
        action="spawn_candidates",
        camera_target="candidate_forge",
        overlay="candidate_blueprints",
        candidate_ids=["A", "B", "C"],
        emphasis="design",
    )
    return AgentEvent(
        sequence=sequence,
        agent="Nano Designer",
        status="complete",
        summary="Forged A 48 nm/-8 mV, B 92 nm/+22 mV, and C 61 nm/-4 mV inside the bounded design envelope.",
        evidence_ids=artifact.evidence_ids,
        scene_action=patch.action,
        artifact=artifact,
        scene_patch=patch,
    )


def simulator_event(sequence: int, results: list[SimulationResult]) -> AgentEvent:
    by_id = {result.candidate.id: result for result in results}
    b, c = by_id["B"], by_id["C"]
    artifact = AgentArtifact(
        kind="distribution_comparison",
        title="24-hour distribution comparison",
        detail="The deterministic twin compares tumour payload against liver and kidney accumulation.",
        metrics=[
            ArtifactMetric(label="C tumour payload", value=_percent(c.tumour_payload_release), unit="%", tone="good"),
            ArtifactMetric(label="C liver / kidney", value=f"{_percent(c.liver_accumulation)} / {_percent(c.kidney_accumulation)}", unit="%", tone="good"),
            ArtifactMetric(label="B liver accumulation", value=_percent(b.liver_accumulation), unit="%", tone="critical"),
        ],
        confidence=c.evidence_confidence,
        evidence_ids=["SIM-MODEL-DETERMINISTIC-V1"],
    )
    patch = ScenePatch(
        action="run_particle_paths",
        camera_target="tumour_core",
        overlay="distribution_paths",
        candidate_ids=["A", "B", "C"],
        simulation_hour=24,
        emphasis="delivery",
    )
    return AgentEvent(
        sequence=sequence,
        agent="Twin Simulator",
        status="complete",
        summary=(
            f"At 24 h, C delivered {_percent(c.tumour_payload_release)}% payload with "
            f"{_percent(c.liver_accumulation)}% liver/{_percent(c.kidney_accumulation)}% kidney accumulation; "
            f"B reached {_percent(b.liver_accumulation)}% liver accumulation."
        ),
        evidence_ids=artifact.evidence_ids,
        scene_action=patch.action,
        artifact=artifact,
        scene_patch=patch,
    )


def safety_event(sequence: int, results: list[SimulationResult]) -> AgentEvent:
    rejected = next(result for result in results if result.decision == "rejected")
    preferred = next(result for result in results if result.decision == "preferred")
    artifact = AgentArtifact(
        kind="safety_decision",
        title="B quarantined · C preferred",
        detail="Candidate B breaches the 45% synthetic liver ceiling. The steward preserves C but cannot approve it.",
        metrics=[
            ArtifactMetric(label="B liver", value=_percent(rejected.liver_accumulation), unit="%", tone="critical"),
            ArtifactMetric(label="Policy ceiling", value=45, unit="%", tone="warning"),
            ArtifactMetric(label="C safety margin", value=_percent(preferred.safety_margin), unit="%", tone="good"),
        ],
        confidence=rejected.evidence_confidence,
        evidence_ids=["POLICY-NANO-SAFETY-V1"],
    )
    patch = ScenePatch(
        action="reject_candidate",
        camera_target="liver_sink",
        overlay="safety_quarantine",
        candidate_ids=[rejected.candidate.id],
        simulation_hour=18,
        emphasis="risk",
    )
    return AgentEvent(
        sequence=sequence,
        agent="Safety Steward",
        status="complete",
        summary=(
            f"Rejected {rejected.candidate.id}: liver accumulation {_percent(rejected.liver_accumulation)}% "
            f"exceeds the 45% policy ceiling; preserved {preferred.candidate.id} for human review."
        ),
        evidence_ids=artifact.evidence_ids,
        scene_action=patch.action,
        artifact=artifact,
        scene_patch=patch,
    )


def approval_boundary_event(sequence: int) -> AgentEvent:
    artifact = AgentArtifact(
        kind="approval_boundary",
        title="Human authority required",
        detail="Evidence is complete, but voice and agents remain unable to approve the research mission.",
        metrics=[ArtifactMetric(label="Autonomous approval", value="BLOCKED", tone="critical")],
        confidence=1,
        evidence_ids=["APPROVAL-POLICY-V1"],
    )
    patch = ScenePatch(
        action="show_approval_membrane",
        camera_target="approval_boundary",
        overlay="approval_membrane",
        emphasis="authority",
    )
    return AgentEvent(
        sequence=sequence,
        agent="Safety Steward",
        status="blocked",
        summary="Evidence complete. Autonomous execution is blocked at the explicit human authority boundary.",
        evidence_ids=artifact.evidence_ids,
        scene_action=patch.action,
        artifact=artifact,
        scene_patch=patch,
    )


def event_contract_for_node(node: str, results: list[SimulationResult]) -> AgentEvent | None:
    factories = {
        "evidence_scout": lambda: evidence_event(0, 0),
        "nano_designer": lambda: designer_event(0),
        "twin_simulator": lambda: simulator_event(0, results),
        "safety_steward": lambda: safety_event(0, results),
    }
    factory = factories.get(node)
    return factory() if factory else None
