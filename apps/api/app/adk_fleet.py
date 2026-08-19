"""Google ADK fleet definition for the governed Nano Safety mission.

Imports are lazy so the deterministic judge fallback stays operational when ADK or
Google credentials are unavailable. Building the fleet never executes a model call.
"""

from dataclasses import asdict
from importlib import metadata
from typing import Any

from .nano_simulator import DEFAULT_CANDIDATES, run_comparison, simulate


VISIBLE_AGENTS = (
    {"name": "evidence_scout", "visible_name": "Evidence Scout", "scene_action": "focus_clone"},
    {"name": "nano_designer", "visible_name": "Nano Designer", "scene_action": "spawn_candidates"},
    {"name": "twin_simulator", "visible_name": "Twin Simulator", "scene_action": "run_particle_paths"},
    {"name": "safety_steward", "visible_name": "Safety Steward", "scene_action": "show_approval_membrane"},
)


def retrieve_synthetic_clone_evidence(clone_id: str) -> dict[str, Any]:
    """Retrieve bounded synthetic evidence for a demonstration clone."""
    if clone_id.upper() != "R7":
        return {"status": "not_found", "synthetic_research_only": True, "evidence_ids": []}
    return {
        "status": "grounded",
        "clone_id": "R7",
        "phenotype": "synthetic_resistant_clone",
        "persistence_signal": 0.31,
        "evidence_ids": ["SYN-CLONE-R7", "SYN-ASSAY-42"],
        "synthetic_research_only": True,
    }


def design_bounded_nano_candidates() -> dict[str, Any]:
    """Return the three candidates inside the approved synthetic parameter envelope."""
    return {
        "candidates": [asdict(candidate) for candidate in DEFAULT_CANDIDATES],
        "evidence_ids": ["PARAM-ENVELOPE-V1"],
        "synthetic_research_only": True,
    }


def simulate_nano_candidate(candidate_id: str) -> dict[str, Any]:
    """Run the deterministic research simulator for one known candidate."""
    candidate = next((item for item in DEFAULT_CANDIDATES if item.id == candidate_id.upper()), None)
    if candidate is None:
        return {"status": "rejected_input", "reason": "Unknown candidate identifier."}
    result = simulate(candidate)
    return {"status": "simulated", **asdict(result), "synthetic_research_only": True}


def apply_nano_safety_policy() -> dict[str, Any]:
    """Apply deterministic safety policy; this tool cannot approve a mission."""
    results = run_comparison()
    preferred = next(result for result in results if result.decision == "preferred")
    rejected = [result.candidate.id for result in results if result.decision == "rejected"]
    return {
        "preferred_candidate_id": preferred.candidate.id,
        "rejected_candidate_ids": rejected,
        "policy_version": "nano-safety-v1",
        "human_approval_required": True,
        "approval_granted": False,
        "synthetic_research_only": True,
    }


def build_adk_fleet(model: str):
    """Build four real ADK agents as an explicit ADK 2 graph workflow."""
    from google.adk import Agent, Workflow

    evidence_scout = Agent(
        name="evidence_scout",
        model=model,
        description="Grounds the mission in synthetic clone evidence and identifiers.",
        instruction=(
            "You are Evidence Scout. Call retrieve_synthetic_clone_evidence for clone R7. "
            "Report only returned synthetic evidence IDs. Never make clinical claims."
        ),
        tools=[retrieve_synthetic_clone_evidence],
        output_key="evidence_scout_result",
    )
    nano_designer = Agent(
        name="nano_designer",
        model=model,
        description="Designs candidates only inside the bounded synthetic parameter envelope.",
        instruction=(
            "You are Nano Designer. Call design_bounded_nano_candidates exactly once. "
            "Do not invent or modify candidate parameters."
        ),
        tools=[design_bounded_nano_candidates],
        output_key="nano_designer_result",
    )
    twin_simulator = Agent(
        name="twin_simulator",
        model=model,
        description="Runs deterministic tumour delivery and off-target simulations.",
        instruction=(
            "You are Twin Simulator. Call simulate_nano_candidate for A, B, and C. "
            "Compare returned values without changing them."
        ),
        tools=[simulate_nano_candidate],
        output_key="twin_simulator_result",
    )
    safety_steward = Agent(
        name="safety_steward",
        model=model,
        description="Applies policy, rejects unsafe research conclusions, and stops for a human.",
        instruction=(
            "You are Safety Steward. Call apply_nano_safety_policy. Preserve its rejection and "
            "preferred candidate. You cannot approve; always stop at human approval."
        ),
        tools=[apply_nano_safety_policy],
        output_key="safety_steward_result",
    )
    return Workflow(
        name="oncotwin_nano_safety_fleet",
        edges=[("START", evidence_scout, nano_designer, twin_simulator, safety_steward)],
    )


def adk_runtime_status(enabled: bool, model: str) -> dict[str, Any]:
    try:
        version = metadata.version("google-adk")
        fleet = build_adk_fleet(model)
        return {
            "installed": True,
            "enabled": enabled,
            "version": version,
            "model": model,
            "coordinator": fleet.name,
            "workflow": "ADK2GraphWorkflow",
            "visible_agents": list(VISIBLE_AGENTS),
            "model_call_executed": False,
            "fallback": "deterministic_mission_service",
        }
    except (ImportError, metadata.PackageNotFoundError) as exc:
        return {
            "installed": False,
            "enabled": False,
            "reason": type(exc).__name__,
            "visible_agents": list(VISIBLE_AGENTS),
            "model_call_executed": False,
            "fallback": "deterministic_mission_service",
        }
