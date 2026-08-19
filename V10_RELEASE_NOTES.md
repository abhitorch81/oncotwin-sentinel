# OncoTwin V10 — Seven DataHub-Native Cancer Context Twins

V10 preserves the V9 visual experience and removes its largest judge-facing
limitation: the six extension missions no longer share a surrogate catalog
asset. Every condition now has a dedicated BigQuery and DataHub identity.

## Canonical condition products

| Condition | Canonical DataHub dataset |
|---|---|
| Biomarker Completeness Crisis | `oncotwin.progression_features` |
| Tumour-State Progression Surge | `oncotwin.tumour_state_transitions` |
| Cancer Cohort Drift | `oncotwin.cohort_drift_metrics` |
| Genomic Schema Mutation | `oncotwin.genomic_schema_contract_events` |
| Multi-omic Biomarker Discordance | `oncotwin.multi_omic_biomarker_evidence` |
| Protein Conformation Evidence Rift | `oncotwin.protein_conformation_states` |
| Tumour Microenvironment Escape | `oncotwin.spatial_microenvironment_states` |

`scripts/03_seed_bigquery.sh` creates the products with generating SQL.
`scripts/06_ingest_bigquery.sh` ingests schema, profiles, query metadata and
available lineage. `scripts/17_bootstrap_datahub_context.sh` attaches the
OncoTwin domain, owners, tags, contracts and explicit upstream relationships.

## Proof contract

`GET /api/datahub/proof?case_id=<condition>` executes six read-only MCP calls:

1. `search`
2. `get_entities`
3. `list_schema_fields`
4. upstream `get_lineage`
5. downstream `get_lineage`
6. `get_dataset_queries`

The response includes the exact URN, owner, tags, contract, measured latency,
incident count and SHA-256 evidence receipt. Proof capture performs zero writes.

## Governed action contract

After explicit human approval, each live mission can create and resolve only its
own title-scoped custom incident on its own canonical asset. The workflow
verifies that the condition incident is gone and leaves unrelated incidents
untouched. Verified replay never repeats the mutation.

## Honest boundary

- Live: DataHub identity, ownership, tags, schema, contract properties, lineage,
  generating queries and condition incident lifecycle.
- Simulated: cancer biology, protein state, spatial response, RL consequence and
  counterfactual recovery animation.
- Never claimed: diagnosis, treatment selection, molecular-dynamics prediction
  or patient-specific clinical validity.

## Verification

Run after deployment:

```bash
export APP_URL="$(gcloud run services describe oncotwin-mission-control \
  --region="${GCP_REGION}" --format='value(status.url)')"
bash scripts/14_verify_ui_version.sh
bash scripts/18_verify_all_datahub_conditions.sh
```

The final command must print `datahub_native_conditions: 7/7` and seven unique
URN/receipt pairs.
