# OncoTwin 3D V9 — Cancer Context Universe

V9 expands the four-condition hackathon demo into seven cancer-data safety
missions. It remains a research-only application and does not diagnose disease,
predict patient outcomes or recommend treatment.

| # | Condition | 3D visual grammar | DataHub safety role |
|---|---|---|---|
| 01 | Biomarker Completeness Crisis | biomarker signal constellation | live schema, quality, lineage and approved incident recovery |
| 02 | Tumour-State Progression Surge | evolving cell-state chain | progression provenance and research-review boundary |
| 03 | Cancer Cohort Drift | distribution wavefront | training/serving lineage and retraining gate |
| 04 | Genomic Schema Mutation | breaking contract columns | metadata-aware code generation and consumer block |
| 05 | Multi-omic Biomarker Discordance | RNA, variant and protein modules out of phase | evidence quarantine, ownership and provenance reconciliation |
| 06 | Protein Conformation Evidence Rift | schematic folding backbone with state rift | sequence-to-structure model lineage and score freeze |
| 07 | Tumour Microenvironment Escape | tumour core, immune field and barrier breach | spatial assay provenance and review gate |

## Truth boundary

- Green graph nodes and proof receipts represent catalog identity, schema,
  lineage and incidents read from DataHub in live mode.
- Red waves and biological state changes are counterfactual simulations.
- Amber nodes are proposed startup-extension data products. They are not
  presented as already ingested assets.
- The Protein Conformation world is a schematic provenance visualization, not
  a protein-folding predictor.
- Only the existing Biomarker Completeness mission can reach the guarded live
  incident-resolution path, and it still requires the operator approval secret.

## Deploy the update

From the extracted project directory:

```bash
export GCP_PROJECT_ID="project-1f5f7d56-1029-4c78-a68"
export GCP_REGION="asia-south1"
export GCP_ZONE="asia-south1-a"
bash scripts/05_deploy_oncotwin.sh
bash scripts/14_verify_ui_version.sh
```

The verification command must report `ui_version: 9.0.0`. Hard-refresh the
browser after deployment so the V9 JavaScript and CSS cache keys are loaded.

