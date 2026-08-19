"""Research-only reinforcement-learning controller for OncoTwin mission simulations.

The policy controls data/ML safety actions.  It never recommends patient treatment.
Biological values are synthetic digital-twin telemetry used to make the safety
environment legible to judges.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random
from typing import Any

from .condition_registry import condition


@dataclass
class TwinState:
    data_trust: int
    model_risk: float
    malignant_fraction: float
    null_rate: float = 0.0
    drift_score: float = 0.0
    schema_compatible: bool = True
    model_blocked: bool = False
    repaired: bool = False

    def public(self) -> dict[str, Any]:
        return asdict(self)


MISSION_CASES: dict[str, dict[str, Any]] = {
    "feature_quality": {
        "title": "Biomarker Completeness Crisis",
        "cohort": "LUAD",
        "challenge": "Production ML Agents",
        "failure": "Missing MKI67 / EPCAM / VIM biomarker feature values",
        "datahub": ["get_entities", "list_schema_fields", "get_lineage", "get_dataset_queries"],
        "actions": ["continue", "monitor", "block_model", "repair_features", "request_review"],
        "initial": TwinState(61, 0.86, 0.43, null_rate=0.18),
        "safe_action": "block_model",
        "repair_action": "repair_features",
        "state_arc": ["complete", "degraded", "repaired"],
    },
    "cancer_progression": {
        "title": "Tumour-State Progression Surge",
        "cohort": "LIHC",
        "challenge": "Open / Wildcard",
        "failure": "Synthetic malignant-cell fraction rises across twin states",
        "datahub": ["search", "get_entities", "get_lineage"],
        "actions": ["continue", "monitor", "flag_research_review", "freeze_inference", "request_review"],
        "initial": TwinState(82, 0.73, 0.43),
        "safe_action": "flag_research_review",
        "repair_action": "monitor",
        "state_arc": ["baseline", "regional", "metastatic-like simulation"],
    },
    "model_drift": {
        "title": "Cancer Cohort Drift",
        "cohort": "KIRC",
        "challenge": "Production ML Agents",
        "failure": "Feature distribution diverges from governed training context",
        "datahub": ["get_entities", "get_lineage", "get_dataset_queries"],
        "actions": ["continue", "monitor", "block_model", "request_retrain", "request_review"],
        "initial": TwinState(68, 0.91, 0.35, drift_score=0.77),
        "safe_action": "block_model",
        "repair_action": "request_retrain",
        "state_arc": ["aligned", "diverging", "retrain-gated"],
    },
    "schema_mutation": {
        "title": "Genomic Schema Mutation",
        "cohort": "COAD",
        "challenge": "Metadata-Aware Code Generation",
        "failure": "Upstream expression field becomes incompatible with feature SQL",
        "datahub": ["list_schema_fields", "get_lineage", "get_dataset_queries"],
        "actions": ["continue", "monitor", "block_consumers", "generate_patch", "request_review"],
        "initial": TwinState(54, 0.88, 0.35, schema_compatible=False),
        "safe_action": "block_consumers",
        "repair_action": "generate_patch",
        "state_arc": ["compatible", "breaking", "patched"],
    },
    "biomarker_discordance": {
        "title": "Multi-omic Biomarker Discordance",
        "cohort": "PAAD",
        "challenge": "Agents That Do Real Work",
        "failure": "RNA, variant annotation and protein evidence disagree on biomarker state",
        "datahub": ["search", "get_entities", "list_schema_fields", "get_lineage"],
        "actions": ["continue", "monitor", "quarantine_biomarker", "reconcile_evidence", "request_review"],
        "initial": TwinState(58, 0.84, 0.30, drift_score=0.64),
        "safe_action": "quarantine_biomarker",
        "repair_action": "reconcile_evidence",
        "state_arc": ["concordant", "discordant", "reconciled"],
    },
    "protein_conformation": {
        "title": "Protein Conformation Evidence Rift",
        "cohort": "SKCM",
        "challenge": "Open / Wildcard",
        "failure": "A schematic protein-state score changes without governed structure-model provenance",
        "datahub": ["search", "get_entities", "get_lineage", "get_dataset_queries"],
        "actions": ["continue", "monitor", "freeze_structure_score", "verify_structure_provenance", "request_review"],
        "initial": TwinState(63, 0.87, 0.32, drift_score=0.72),
        "safe_action": "freeze_structure_score",
        "repair_action": "verify_structure_provenance",
        "state_arc": ["native-like", "intermediate", "provenance-rift"],
    },
    "microenvironment_escape": {
        "title": "Tumour Microenvironment Escape",
        "cohort": "GBM",
        "challenge": "Production ML Agents",
        "failure": "Spatial immune-cell context shifts while the bulk progression score appears stable",
        "datahub": ["search", "get_entities", "list_schema_fields", "get_lineage"],
        "actions": ["continue", "monitor", "flag_spatial_review", "reconcile_spatial_context", "request_review"],
        "initial": TwinState(60, 0.82, 0.45, drift_score=0.68),
        "safe_action": "flag_spatial_review",
        "repair_action": "reconcile_spatial_context",
        "state_arc": ["inflamed", "immune-excluded", "escape-risk"],
    },
}


class SafetyQLearner:
    """Tiny deterministic Q-learning policy used for the digital-twin simulation."""

    def __init__(self, case_id: str, seed: int = 81):
        self.case_id = case_id
        self.case = MISSION_CASES[case_id]
        self.actions: list[str] = self.case["actions"]
        self.rand = Random(seed + list(MISSION_CASES).index(case_id))
        self.q: dict[tuple[tuple[int, int, int, int], str], float] = {}

    @staticmethod
    def bucket(s: TwinState) -> tuple[int, int, int, int]:
        return (
            int(s.data_trust < 70),
            int(s.model_risk >= 0.75),
            int(s.null_rate >= 0.10 or s.drift_score >= 0.60),
            int(not s.schema_compatible),
        )

    def reward(self, state: TwinState, action: str) -> float:
        unsafe = (
            state.model_risk >= 0.75
            or state.null_rate >= 0.10
            or state.drift_score >= 0.60
            or not state.schema_compatible
            or state.malignant_fraction >= 0.35
        )
        if action == self.case["safe_action"]:
            return 12.0 if unsafe else 3.0
        if action == self.case["repair_action"]:
            return 8.0 if unsafe else 2.0
        if action == "request_review":
            return 5.0
        if action == "monitor":
            return 2.0 if not unsafe else -4.0
        if action == "continue":
            return -15.0 if unsafe else 4.0
        return 1.0

    def train(self, episodes: int = 700) -> None:
        state: TwinState = self.case["initial"]
        key = self.bucket(state)
        for episode in range(episodes):
            epsilon = max(0.03, 0.34 * (1 - episode / episodes))
            if self.rand.random() < epsilon:
                action = self.rand.choice(self.actions)
            else:
                action = max(self.actions, key=lambda a: self.q.get((key, a), 0.0))
            old = self.q.get((key, action), 0.0)
            target = self.reward(state, action)
            self.q[(key, action)] = old + 0.18 * (target - old)

    def decide(self, state: TwinState) -> dict[str, Any]:
        self.train()
        key = self.bucket(state)
        ranked = sorted(
            ((action, round(self.q.get((key, action), 0.0), 3)) for action in self.actions),
            key=lambda item: item[1],
            reverse=True,
        )
        return {
            "algorithm": "tabular-q-learning",
            "episodes": 700,
            "state_bucket": key,
            "action": ranked[0][0],
            "q_value": ranked[0][1],
            "reward": self.reward(state, ranked[0][0]),
            "ranked_actions": ranked,
        }


def simulate_transition(case_id: str, state: TwinState, action: str) -> TwinState:
    """Apply an operational safety action to the synthetic digital twin."""
    next_state = TwinState(**state.public())
    if action in {
        "block_model", "block_consumers", "freeze_inference",
        "quarantine_biomarker", "freeze_structure_score", "flag_spatial_review",
    }:
        next_state.model_blocked = True
        next_state.model_risk = max(0.25, next_state.model_risk - 0.28)
        next_state.data_trust = min(100, next_state.data_trust + 7)
    elif action == "flag_research_review":
        next_state.model_blocked = True
        next_state.model_risk = max(0.30, next_state.model_risk - 0.20)
        next_state.data_trust = min(100, next_state.data_trust + 5)
    elif action in {
        "repair_features", "generate_patch", "request_retrain",
        "reconcile_evidence", "verify_structure_provenance", "reconcile_spatial_context",
    }:
        next_state.repaired = True
        next_state.null_rate = 0.0
        next_state.drift_score = min(next_state.drift_score, 0.18)
        next_state.schema_compatible = True
        next_state.model_risk = max(0.18, next_state.model_risk - 0.48)
        next_state.data_trust = min(100, next_state.data_trust + 24)
    return next_state


def mission_catalog() -> list[dict[str, Any]]:
    result = []
    for case_id, case in MISSION_CASES.items():
        catalog = condition(case_id)
        result.append({
            "case_id": case_id,
            "title": case["title"],
            "default_cohort": case["cohort"],
            "challenge": case["challenge"],
            "failure": case["failure"],
            "datahub_tools": [
                "search", "get_entities", "list_schema_fields",
                "get_lineage_upstream", "get_lineage_downstream", "get_dataset_queries",
            ],
            "asset_name": catalog["asset_name"],
            "asset_owner": catalog["owner"],
            "data_contract": catalog["contract"],
            "proof_endpoint": f"/api/datahub/proof?case_id={case_id}",
            "writeback": "guarded-condition-incident",
            "datahub_native": True,
            "state_arc": case["state_arc"],
            "research_only": True,
        })
    return result
