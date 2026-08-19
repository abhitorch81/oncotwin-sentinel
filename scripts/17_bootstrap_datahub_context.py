#!/usr/bin/env python3
"""Attach V10 ownership, tags, contracts and lineage to all seven assets."""

from __future__ import annotations

import os

from datahub.emitter.mce_builder import make_dataset_urn, make_domain_urn, make_tag_urn, make_user_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetLineageTypeClass,
    DatasetPropertiesClass,
    DomainPropertiesClass,
    DomainsClass,
    GlobalTagsClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
    TagAssociationClass,
    TagPropertiesClass,
    UpstreamClass,
    UpstreamLineageClass,
)


PROJECT = os.environ["GCP_PROJECT_ID"]
SERVER = os.environ["DATAHUB_GMS_URL"].rstrip("/")
TOKEN = os.environ["DATAHUB_GMS_TOKEN"]
DOMAIN_URN = make_domain_urn("oncotwin-cancer-context")
OWNER_URN = make_user_urn("oncotwin-agent")

ASSETS = {
    "feature_quality": {
        "table": "progression_features",
        "title": "Biomarker Completeness Crisis",
        "description": "Non-null biomarker feature product protecting the OncoTwin progression consumer.",
        "contract": "MKI67, EPCAM and VIM derived signals must be non-null.",
        "tags": ["CancerContext", "BiomarkerQuality", "ProductionML"],
        "upstreams": ["gene_expression_summary"],
    },
    "cancer_progression": {
        "table": "tumour_state_transitions",
        "title": "Tumour-State Progression Surge",
        "description": "Research-only tumour-state transition evidence with source-score and model provenance.",
        "contract": "Every transition preserves cohort, source score and model version provenance.",
        "tags": ["CancerContext", "TumourState", "ResearchOnly"],
        "upstreams": ["progression_scores"],
    },
    "model_drift": {
        "table": "cohort_drift_metrics",
        "title": "Cancer Cohort Drift",
        "description": "Training-to-serving cohort drift metrics used by the production ML retraining gate.",
        "contract": "Feature drift must remain below the governed retraining threshold.",
        "tags": ["CancerContext", "ModelDrift", "ProductionML"],
        "upstreams": ["progression_scores"],
    },
    "schema_mutation": {
        "table": "genomic_schema_contract_events",
        "title": "Genomic Schema Mutation",
        "description": "Schema compatibility events that ground metadata-aware genomic SQL generation.",
        "contract": "Breaking field changes require downstream impact review before consumption.",
        "tags": ["CancerContext", "SchemaContract", "CodeGeneration"],
        "upstreams": ["gene_expression_summary"],
    },
    "biomarker_discordance": {
        "table": "multi_omic_biomarker_evidence",
        "title": "Multi-omic Biomarker Discordance",
        "description": "RNA, variant and protein evidence with explicit concordance and provenance state.",
        "contract": "Every biomarker exposes RNA, variant, protein and concordance evidence.",
        "tags": ["CancerContext", "MultiOmic", "Biomarker"],
        "upstreams": ["gene_expression_summary"],
    },
    "protein_conformation": {
        "table": "protein_conformation_states",
        "title": "Protein Conformation Evidence Rift",
        "description": "Schematic research structure evidence; provenance demonstration, not folding prediction.",
        "contract": "Every score retains sequence, structure-model and source-evidence provenance.",
        "tags": ["CancerContext", "ProteinStructure", "Provenance"],
        "upstreams": ["multi_omic_biomarker_evidence"],
    },
    "microenvironment_escape": {
        "table": "spatial_microenvironment_states",
        "title": "Tumour Microenvironment Escape",
        "description": "Spatial immune-context states derived from governed single-cell cluster evidence.",
        "contract": "Spatial immune context is reconciled with source cell clusters before scoring.",
        "tags": ["CancerContext", "SpatialOmics", "ImmuneEscape"],
        "upstreams": ["cell_clusters"],
    },
}


def urn(table: str) -> str:
    return make_dataset_urn("bigquery", f"{PROJECT}.oncotwin.{table}", "PROD")


def emit(emitter: DatahubRestEmitter, entity_urn: str, aspect: object) -> None:
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=entity_urn, aspect=aspect))


def main() -> None:
    emitter = DatahubRestEmitter(gms_server=SERVER, token=TOKEN)
    emitter.test_connection()
    emit(emitter, DOMAIN_URN, DomainPropertiesClass(name="OncoTwin Cancer Context", description="Governed research-only cancer ML digital-twin assets."))
    all_tags = sorted({tag for spec in ASSETS.values() for tag in spec["tags"]} | {"Deidentified", "HackathonDemo"})
    for tag in all_tags:
        emit(emitter, make_tag_urn(tag), TagPropertiesClass(name=tag, description=f"OncoTwin V10 context tag: {tag}."))
    for case_id, spec in ASSETS.items():
        asset_urn = urn(spec["table"])
        emit(emitter, asset_urn, DatasetPropertiesClass(
            name=spec["table"],
            description=f"{spec['title']}. {spec['description']} Research demonstration only; not clinical advice.",
            customProperties={
                "oncotwin.condition_id": case_id,
                "oncotwin.condition": spec["title"],
                "oncotwin.data_contract": spec["contract"],
                "oncotwin.research_only": "true",
                "oncotwin.proof_endpoint": f"/api/datahub/proof?case_id={case_id}",
            },
        ))
        emit(emitter, asset_urn, DomainsClass(domains=[DOMAIN_URN]))
        emit(emitter, asset_urn, OwnershipClass(owners=[OwnerClass(owner=OWNER_URN, type=OwnershipTypeClass.DATAOWNER)]))
        emit(emitter, asset_urn, GlobalTagsClass(tags=[TagAssociationClass(tag=make_tag_urn(tag)) for tag in [*spec["tags"], "Deidentified", "HackathonDemo"]]))
        emit(emitter, asset_urn, UpstreamLineageClass(upstreams=[
            UpstreamClass(dataset=urn(upstream), type=DatasetLineageTypeClass.TRANSFORMED)
            for upstream in spec["upstreams"]
        ]))
        print(f"contextualized {case_id}: {asset_urn}")
    emitter.close()
    print("Seven DataHub-native cancer-context assets are ready.")


if __name__ == "__main__":
    main()
