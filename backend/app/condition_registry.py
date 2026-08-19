"""Canonical DataHub contracts for the OncoTwin V11 decision multiverse."""

from __future__ import annotations

from typing import Any


def _spec(title: str, asset: str, owner: str, tags: list[str], contract: str, fields: list[str]) -> dict[str, Any]:
    return {"title": title, "asset_name": asset, "owner": owner, "tags": tags,
            "contract": contract, "fields": fields, "query_evidence": True}


CONDITION_REGISTRY: dict[str, dict[str, Any]] = {
    "feature_quality": _spec("Trial Data Integrity Crisis", "progression_features", "Clinical Data Reliability", ["trial-integrity", "research-only"], "Biomarker features must be complete before ML consumption.", ["patient_key", "cluster_id", "stage", "proliferation_signal", "epithelial_signal", "mesenchymal_signal"]),
    "cancer_progression": _spec("MET Resistance Evolution", "tumour_state_transitions", "Thoracic Translational AI", ["MET", "resistance", "research-only"], "Resistance states require provenance and human review.", ["patient_key", "state", "malignant_fraction", "observed_at"]),
    "model_drift": _spec("Digital Pathology Domain Shift", "cohort_drift_metrics", "Pathology ML Assurance", ["digital-pathology", "domain-shift"], "Inference is gated when domain drift exceeds the governed threshold.", ["cohort", "scanner", "drift_score", "measured_at"]),
    "schema_mutation": _spec("Genomic Schema Mutation", "genomic_schema_contract_events", "Genomics Platform", ["genomics", "contract"], "Breaking schema changes must block downstream consumers.", ["asset_urn", "field_name", "compatibility", "observed_at"]),
    "biomarker_discordance": _spec("Multi-omic Discordance", "multi_omic_biomarker_evidence", "Precision Oncology Evidence", ["multi-omic", "discordance"], "RNA, variant and protein evidence must be reconciled before use.", ["patient_key", "gene", "rna_state", "variant_state", "protein_state"]),
    "protein_conformation": _spec("ADC Payload Resistance", "protein_conformation_states", "ADC Research Safety", ["ADC", "payload-resistance"], "Structure and response signals require governed provenance.", ["target", "structure_state", "payload_signal", "confidence"]),
    "microenvironment_escape": _spec("Spatial Immune Escape", "spatial_microenvironment_states", "Spatial Oncology", ["spatial-omics", "immune-escape"], "Spatial immune context must accompany progression claims.", ["region", "cell_state", "immune_distance", "escape_score"]),
    "ctdna_mrd_rebound": _spec("ctDNA MRD Rebound", "ctdna_mrd_signals", "Liquid Biopsy Reliability", ["ctDNA", "MRD"], "MRD rebound signals require orthogonal confirmation and human review.", ["patient_key", "variant", "vaf", "trend", "sample_time"]),
    "bispecific_safety": _spec("Bispecific Safety Signal", "bispecific_safety_signals", "Immunotherapy Safety", ["bispecific", "safety"], "Cytokine and toxicity signals activate a non-clinical safety gate.", ["study_id", "cytokine", "grade", "signal_time"]),
    "cart_antigen_escape": _spec("CAR-T Antigen Escape", "cart_antigen_states", "Cell Therapy Research", ["CAR-T", "antigen-escape"], "Antigen-loss claims require multi-assay validation.", ["patient_key", "antigen", "expression", "clone_fraction"]),
    "neoantigen_vaccine_drift": _spec("Neoantigen Vaccine Drift", "neoantigen_target_drift", "Cancer Vaccine Research", ["neoantigen", "vaccine"], "Target drift must pause research hypotheses until refreshed evidence is reviewed.", ["patient_key", "peptide", "clone_frequency", "presentation_score"]),
    "radiopharmaceutical_mismatch": _spec("Radiopharmaceutical Target Mismatch", "theranostic_target_alignment", "Theranostics Assurance", ["radiopharmaceutical", "theranostics"], "Imaging and target evidence must align before a research claim proceeds.", ["patient_key", "target", "imaging_signal", "tissue_signal"]),
}


def condition(case_id: str) -> dict[str, Any]:
    return CONDITION_REGISTRY[case_id]


def dataset_urn(project: str, case_id: str) -> str:
    asset = condition(case_id)["asset_name"]
    return f"urn:li:dataset:(urn:li:dataPlatform:bigquery,{project}.oncotwin.{asset},PROD)"
