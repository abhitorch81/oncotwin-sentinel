from __future__ import annotations

from typing import Any


# One canonical DataHub dataset per cancer-context mission.  The biological
# measurements are synthetic research telemetry; the catalog identity, schema,
# ownership, quality context and lineage are real in live mode.
CONDITION_REGISTRY: dict[str, dict[str, Any]] = {
    "feature_quality": {
        "asset_name": "progression_features",
        "title": "Biomarker Completeness Crisis",
        "owner": "Thoracic ML",
        "tags": ["CancerContext", "BiomarkerQuality", "ProductionML"],
        "contract": "MKI67, EPCAM and VIM derived signals must be non-null.",
        "fields": ["patient_key", "cluster_id", "stage", "proliferation_signal", "epithelial_signal", "mesenchymal_signal", "generated_at"],
        "query_evidence": True,
    },
    "cancer_progression": {
        "asset_name": "tumour_state_transitions",
        "title": "Tumour-State Progression Surge",
        "owner": "Hepatic AI",
        "tags": ["CancerContext", "TumourState", "ResearchOnly"],
        "contract": "Every transition must preserve cohort, source score and model version provenance.",
        "fields": ["patient_key", "cluster_id", "from_state", "to_state", "transition_probability", "source_progression_score", "model_version", "observed_at"],
        "query_evidence": True,
    },
    "model_drift": {
        "asset_name": "cohort_drift_metrics",
        "title": "Cancer Cohort Drift",
        "owner": "Renal ML",
        "tags": ["CancerContext", "ModelDrift", "ProductionML"],
        "contract": "Population stability and feature drift must remain below the governed retraining threshold.",
        "fields": ["cohort_code", "model_version", "feature_name", "baseline_mean", "serving_mean", "drift_score", "decision", "measured_at"],
        "query_evidence": True,
    },
    "schema_mutation": {
        "asset_name": "genomic_schema_contract_events",
        "title": "Genomic Schema Mutation",
        "owner": "GI Oncology ML",
        "tags": ["CancerContext", "SchemaContract", "CodeGeneration"],
        "contract": "Breaking genomic field changes must be blocked until downstream SQL is regenerated and reviewed.",
        "fields": ["event_id", "source_asset", "field_name", "expected_type", "observed_type", "compatibility", "downstream_asset", "detected_at"],
        "query_evidence": True,
    },
    "biomarker_discordance": {
        "asset_name": "multi_omic_biomarker_evidence",
        "title": "Multi-omic Biomarker Discordance",
        "owner": "Pancreatic Multi-omics",
        "tags": ["CancerContext", "MultiOmic", "Biomarker"],
        "contract": "RNA, variant and protein evidence must expose provenance and concordance before model use.",
        "fields": ["patient_key", "gene", "rna_signal", "variant_call", "protein_signal", "concordance_score", "evidence_state", "evaluated_at"],
        "query_evidence": True,
    },
    "protein_conformation": {
        "asset_name": "protein_conformation_states",
        "title": "Protein Conformation Evidence Rift",
        "owner": "Structural Oncology",
        "tags": ["CancerContext", "ProteinStructure", "Provenance"],
        "contract": "Every structure score must retain sequence, structure-model and source-evidence provenance.",
        "fields": ["protein_id", "gene", "sequence_version", "structure_model", "conformation_state", "confidence_score", "provenance_status", "scored_at"],
        "query_evidence": True,
    },
    "microenvironment_escape": {
        "asset_name": "spatial_microenvironment_states",
        "title": "Tumour Microenvironment Escape",
        "owner": "Spatial Oncology",
        "tags": ["CancerContext", "SpatialOmics", "ImmuneEscape"],
        "contract": "Spatial immune context must be reconciled with cell clusters before progression scoring.",
        "fields": ["region_id", "cluster_id", "cell_type", "immune_distance", "malignant_fraction", "spatial_state", "review_required", "measured_at"],
        "query_evidence": True,
    },
}


def condition(case_id: str) -> dict[str, Any]:
    try:
        return CONDITION_REGISTRY[case_id]
    except KeyError as exc:
        raise ValueError(f"Unknown cancer-context condition: {case_id}") from exc


def dataset_urn(project: str, case_id: str) -> str:
    asset = condition(case_id)["asset_name"]
    return f"urn:li:dataset:(urn:li:dataPlatform:bigquery,{project}.oncotwin.{asset},PROD)"
