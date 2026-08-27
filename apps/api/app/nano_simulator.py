from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math


@dataclass(frozen=True)
class NanoCandidate:
    id: str
    name: str
    particle_size_nm: float
    surface_charge_mv: float
    ligand_affinity: float
    stealth_score: float
    release_half_life_hours: float
    biodegradability: float


@dataclass(frozen=True)
class NanoResult:
    candidate: NanoCandidate
    tumour_penetration: float
    tumour_payload_release: float
    liver_accumulation: float
    kidney_accumulation: float
    evidence_confidence: float
    safety_margin: float
    decision: str
    reason: str


@dataclass(frozen=True)
class NanoSimulationFrame:
    hour: int
    candidate_id: str
    tumour_penetration: float
    tumour_payload_release: float
    liver_accumulation: float
    kidney_accumulation: float


DEFAULT_CANDIDATES = (
    NanoCandidate("A", "Aster-48", 48, -8, .72, .80, 9, .77),
    NanoCandidate("B", "Brimstone-92", 92, 22, .88, .31, 3, .38),
    NanoCandidate("C", "Calyx-61", 61, -4, .91, .89, 12, .86),
)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def simulate(candidate: NanoCandidate) -> NanoResult:
    """Deterministic synthetic model; never a clinical prediction."""
    size_fit = math.exp(-((candidate.particle_size_nm - 58) / 34) ** 2)
    charge_penalty = min(abs(candidate.surface_charge_mv) / 35, 1)
    penetration = _clamp(.42 * size_fit + .34 * candidate.ligand_affinity + .24 * candidate.stealth_score)
    release_fit = math.exp(-((candidate.release_half_life_hours - 10) / 8) ** 2)
    payload = _clamp(.55 * penetration + .30 * release_fit + .15 * candidate.biodegradability)
    liver = _clamp(.58 * charge_penalty + .31 * (1 - candidate.stealth_score) + .11 * (candidate.particle_size_nm / 100))
    kidney = _clamp(.43 * max(0, (65 - candidate.particle_size_nm) / 45) + .32 * charge_penalty + .25 * (1 - candidate.biodegradability))
    confidence = _clamp(.70 + .12 * candidate.ligand_affinity + .10 * candidate.biodegradability)
    margin = _clamp(payload - max(liver, kidney))
    rejected = liver > .45 or kidney > .42 or margin < .20
    decision = "rejected" if rejected else ("preferred" if margin >= .55 else "acceptable")
    reason = (
        "Rejected: synthetic off-target accumulation exceeds the research safety envelope."
        if rejected else
        "Preferred balance of tumour delivery, controlled release, and lower synthetic organ accumulation."
        if decision == "preferred" else
        "Within the synthetic safety envelope, but not the strongest delivery-to-risk balance."
    )
    return NanoResult(candidate, penetration, payload, liver, kidney, confidence, margin, decision, reason)


def run_comparison(candidates=DEFAULT_CANDIDATES) -> list[NanoResult]:
    results = [simulate(candidate) for candidate in candidates]
    safe = [result for result in results if result.decision != "rejected"]
    if safe:
        winner = max(safe, key=lambda result: result.safety_margin)
        results = [
            NanoResult(**{**asdict(result), "candidate": result.candidate,
                          "decision": "preferred" if result.candidate.id == winner.candidate.id else
                                      "acceptable" if result.decision == "preferred" else result.decision,
                          "reason": "Preferred balance of tumour delivery, controlled release, and lower synthetic organ accumulation."
                          if result.candidate.id == winner.candidate.id else result.reason})
            for result in results
        ]
    return results


def _normalized_saturation(hour: int, time_constant: float) -> float:
    if hour <= 0:
        return 0.0
    maximum = 1 - math.exp(-24 / time_constant)
    return (1 - math.exp(-hour / time_constant)) / maximum


def build_timeline(results: list[NanoResult]) -> list[NanoSimulationFrame]:
    """Create deterministic hourly synthetic kinetics ending at each receipt result."""
    frames: list[NanoSimulationFrame] = []
    for hour in range(25):
        for result in results:
            candidate = result.candidate
            penetration_curve = _normalized_saturation(hour, 4.8 + candidate.particle_size_nm / 45)
            release_curve = _normalized_saturation(hour, max(2.5, candidate.release_half_life_hours / math.log(2)))
            liver_curve = (hour / 24) ** 1.35 if candidate.id == "B" else _normalized_saturation(hour, 8.5)
            kidney_curve = _normalized_saturation(hour, 6.2 + candidate.particle_size_nm / 55)
            frames.append(NanoSimulationFrame(
                hour=hour,
                candidate_id=candidate.id,
                tumour_penetration=_clamp(result.tumour_penetration * penetration_curve),
                tumour_payload_release=_clamp(result.tumour_payload_release * release_curve),
                liver_accumulation=_clamp(result.liver_accumulation * liver_curve),
                kidney_accumulation=_clamp(result.kidney_accumulation * kidney_curve),
            ))
    return frames


def receipt_digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode()).hexdigest()
