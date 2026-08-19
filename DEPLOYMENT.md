# Exact GCP Deployment: Start to Finish

This guide assumes a Mac terminal, a Google Cloud project with billing enabled, and permission to create Compute Engine, Cloud Run, BigQuery, IAM, Secret Manager and Artifact Registry resources.

## 1. Unpack and enter the project

From GitHub:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/oncotwin-datahub.git
cd oncotwin-datahub
chmod +x scripts/*.sh
```

Or extract the attached release ZIP and enter its directory before continuing.

## 2. Install and authenticate Google Cloud CLI

Install `gcloud` from the official Google Cloud SDK, then:

```bash
gcloud auth login
gcloud auth application-default login
gcloud projects list
```

Set your values:

```bash
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
export GCP_REGION="asia-south1"
export GCP_ZONE="asia-south1-a"
export DATAHUB_VM_NAME="oncotwin-datahub"
```

Verify:

```bash
bash scripts/00_check_prerequisites.sh
```

## 3. Prepare APIs, network, registry and runtime identity

```bash
bash scripts/01_prepare_gcp.sh
```

This creates:

- `oncotwin-net`
- `oncotwin-subnet` (`10.42.0.0/24`)
- IAP-only SSH firewall access
- private DataHub GMS access from the application subnet
- `oncotwin-agent` runtime service account
- Artifact Registry repository

## 4. Create the DataHub VM

```bash
bash scripts/02_create_datahub_vm.sh
```

The script creates an `e2-standard-4` AMD64 VM with 16 GB RAM, an 80 GB balanced disk and 4 GB swap. Its startup script installs Docker, the DataHub CLI and runs:

```bash
datahub docker quickstart
```

Wait approximately 5–10 minutes. Inspect installation progress:

```bash
gcloud compute ssh oncotwin-datahub \
  --zone=asia-south1-a \
  --tunnel-through-iap \
  --command="sudo journalctl -u google-startup-scripts.service -n 100 --no-pager"
```

Check containers:

```bash
gcloud compute ssh oncotwin-datahub \
  --zone=asia-south1-a \
  --tunnel-through-iap \
  --command="sudo docker ps"
```

Do not continue until the GMS, frontend, MySQL, Kafka and OpenSearch containers are healthy/running.

## 5. Open the DataHub UI securely

In a dedicated terminal:

```bash
bash scripts/11_open_datahub_tunnel.sh
```

Keep it running and open:

```text
http://localhost:9002
```

Quickstart credentials:

```text
username: datahub
password: datahub
```

Change the default password before showing the demo.

## 6. Create the DataHub agent identity and token

For the hackathon, use a DataHub service account for the autonomous workflow rather than a human token. Inside DataHub:

1. Open **Settings → Users & Groups → Service Accounts**.
2. Create `oncotwin-agent`.
3. If your DataHub version exposes **Default View**, scope it to the OncoTwin/oncology assets.
4. Generate an access token for that service account.
5. Give it only a duration that covers the hackathon and store it in your password manager.

In your terminal, while the tunnel is running:

```bash
export DATAHUB_GMS_URL="http://localhost:8088"
export DATAHUB_GMS_TOKEN="PASTE_TOKEN_LOCALLY"
```

Never put the token in GitHub, frontend code, screenshots or chat.

This matches DataHub's recommendation for unattended/agentic workflows. For
this hackathon the stored token is also mounted under the server-only
`DATAHUB_ADMIN_TOKEN` name for approved incident resolution. In production,
split read and admin credentials and narrow each policy.

## 7. Create the demonstration BigQuery data

```bash
bash scripts/03_seed_bigquery.sh
```

Confirm:

```bash
bq ls "${GCP_PROJECT_ID}:oncotwin"
```

Expected tables include:

- `patient_cohorts`
- `cell_clusters`
- `gene_expression_summary`
- `progression_features`
- `progression_scores`
- `quality_events`
- `tumour_state_transitions`
- `cohort_drift_metrics`
- `genomic_schema_contract_events`
- `multi_omic_biomarker_evidence`
- `protein_conformation_states`
- `spatial_microenvironment_states`

## 8. Ingest BigQuery metadata into DataHub

Keep the SSH tunnel open. Then run:

```bash
bash scripts/06_ingest_bigquery.sh
bash scripts/17_bootstrap_datahub_context.sh
```

In DataHub search for:

```text
progression_scores
```

Open the datasets and verify schema, profile and lineage tabs. Script 17 attaches the OncoTwin domain, ownership, tags, explicit upstream lineage and machine-readable contract properties to all seven mission assets.

- Domain: `Cancer Progression Research`
- Owner: `OncoTwin Bioinformatics`
- Tags: `CancerProgression`, `Deidentified`, `HackathonDemo`
- `progression_score`: “Research-only model score from 0 to 1; not a clinical diagnosis.”

This improves the Analytics Agent context score and makes the before/after writeback visible.

## 8B. Install the official DataHub Skills on the GCP VM

Run from your Mac:

```bash
bash scripts/15_install_datahub_skills_vm.sh
```

The script installs Gemini CLI, `uvx`, and the official `datahub-project/datahub-skills` package for Gemini CLI on the VM. It does **not** copy your DataHub token.

Then SSH to the VM, export the scoped service-account token for that shell and add DataHub MCP exactly as shown by the script. Start `gemini` and verify:

```text
/skills list
```

Use these judge-friendly prompts:

```text
Find the canonical OncoTwin progression dataset and explain why it is trustworthy.
Trace downstream impact from progression_features.
Find quality issues that could break the progression model.
```

This is the literal official DataHub Skills workflow running on your GCP VM. The web application's Repair Engineer separately executes the same search/quality/lineage pattern against live MCP evidence so the judge UI remains deterministic and auditable.

## 9. Store secrets

Obtain a Google Gemini Developer API key for the unmodified official Analytics Agent. The custom mission-control agents use Vertex AI ADC and do not need this key.

```bash
export GOOGLE_API_KEY="YOUR_GOOGLE_AI_STUDIO_KEY"
export WRITEBACK_APPROVAL_SECRET="$(openssl rand -hex 24)"
bash scripts/04_create_secrets.sh
```

Save `WRITEBACK_APPROVAL_SECRET` in your password manager; the judge operator enters it only when demonstrating approval.

## 10. Deploy OncoTwin Mission Control

For the Cloud Run backend, replace the tunnel URL with the VM's private address automatically by running:

```bash
# Optional Phase 3 native audio. Leave false for the browser-speech fallback.
export GEMINI_LIVE_ENABLED=true
export GEMINI_LIVE_USE_VERTEXAI=false
bash scripts/05_deploy_oncotwin.sh
```

When native audio is enabled with the Developer API, the deploy script binds
`oncotwin-google-api-key` from Secret Manager to the backend only. The browser
connects to `/api/agentic/live`; it never receives the key. Cloud Run's request
timeout is set to 900 seconds while the application rotates Live sessions at
840 seconds. See [docs/GEMINI_LIVE.md](docs/GEMINI_LIVE.md) for the audio and
safety contract. To keep Gemini Live disabled, omit the two exports above.

The command prints the public Cloud Run URL. Open it and confirm the header says:

```text
● LIVE DATAHUB
```

Test the backend:

```bash
export APP_URL="$(gcloud run services describe oncotwin-mission-control --region=asia-south1 --format='value(status.url)')"
bash scripts/07_smoke_test.sh
bash scripts/14_verify_ui_version.sh
bash scripts/18_verify_all_datahub_conditions.sh
```

## 11. Prepare the Analytics Agent BigQuery credential

The current official Analytics Agent BigQuery connector explicitly requests JSON credentials. The provided script creates a narrowly permissioned key for `oncotwin-agent`, immediately uploads it to Secret Manager and removes the temporary local file:

```bash
bash scripts/09_create_bigquery_key_secret.sh
```

Treat service-account keys as temporary. Delete this key after the hackathon.

## 12. Deploy the official DataHub Analytics Agent

```bash
bash scripts/10_deploy_analytics_agent.sh
```

The script:

1. Builds a thin image on top of `ghcr.io/datahub-project/analytics-agent:main`.
2. Connects it privately to DataHub GMS.
3. Connects it to the `oncotwin` BigQuery dataset.
4. Uses Google Gemini as the LLM provider.
5. Adds the Analytics Agent URL to Mission Control.

Open the printed Analytics Agent URL. In its connection settings, run both connection tests.

## 13. Test the exact analytics scenario

Ask:

```text
Compare average progression score by cancer stage and render a bar chart.
```

Then:

```text
Compare MKI67 and EPCAM mean expression by stage.
```

Expand the tool and SQL steps. Confirm that:

- DataHub context was searched first.
- The SQL references `oncotwin` tables.
- A chart appears.
- The context-quality score is visible.

Now type:

```text
/improve-context
```

Approve one safe documentation proposal. Refresh the asset in DataHub and show the change.

## 14. Test the MCP-governed workflow

In Mission Control, ask:

```text
Which cancer progression datasets are trustworthy, and what downstream models would be affected by a completeness issue?
```

Verify six visible steps:

1. Catalog Scout — `search`
2. Quality Sentinel — `get_entities`
3. Lineage Guardian — `get_lineage`
4. Progression Analyst — Agent Context Kit + LangChain + Gemini grounded narrative
5. Repair Engineer — DataHub Skills quality + lineage workflow, context fingerprint and generated artifact
6. Governance Steward — blocked `update_description` writeback proposal

For a machine-readable proof of the DataHub surfaces wired into the running app:

```bash
curl -s "${APP_URL}/api/datahub/capabilities" | python3 -m json.tool
```

Enter the approval secret and click **Approve once**. Verify the DataHub description changed. The proposal is removed after one commit and cannot be replayed.

## 14B. Run the twelve RL digital-twin cases

The v6 mission deck contains:

1. **Biomarker Completeness Crisis** — live BigQuery FAIL signal → active DataHub incident → lineage blast radius → RL blocks the model → schema-grounded BigQuery repair after human approval → quality PASS → incident resolution → durable DataHub description/tag/custom-property writeback → MCP verification.
2. **Tumour-State Progression Surge** — synthetic malignant-fraction transition → research-review boundary.
3. **Cancer Cohort Drift** — governed training/serving context divergence → model block → retraining request.
4. **Genomic Schema Mutation** — schema mismatch → downstream consumer block → metadata-aware code patch.
5. **Multi-omic Biomarker Discordance** — RNA/variant/protein conflict → biomarker quarantine → provenance reconciliation.
6. **Protein Conformation Evidence Rift** — schematic structure-state provenance change → structure-score freeze.
7. **Tumour Microenvironment Escape** — spatial immune-context shift → spatial review gate.
8. **ctDNA MRD Rebound** — longitudinal liquid-biopsy rebound → orthogonal-validation gate.
9. **Bispecific Safety Signal** — cytokine boundary crossing → non-clinical safety gate.
10. **CAR-T Antigen Escape** — target-antigen loss → response-claim freeze.
11. **Neoantigen Vaccine Drift** — clonal target drift → governed target refresh.
12. **Radiopharmaceutical Target Mismatch** — imaging/tissue disagreement → theranostic-claim block.

All twelve cases use condition-specific live DataHub evidence and may execute a
narrow, human-approved condition-incident lifecycle on their own cataloged
asset. The first case is the flagship full mutation: it additionally repairs
BigQuery, validates the feature contract, writes durable DataHub documentation,
tags and custom properties, and verifies the inherited knowledge through MCP.
The biological response remains a research simulation in every case. All twelve
record timestamped DataHub evidence, twin state, RL state/action/reward and
approval events for safe replay.

After deploying, run the machine-readable end-to-end proof from your Mac:

```bash
export APP_URL="$(gcloud run services describe oncotwin-mission-control \
  --region=asia-south1 --format='value(status.url)')"
export WRITEBACK_APPROVAL_SECRET="YOUR_SAVED_APPROVAL_SECRET"
bash scripts/16_verify_live_rl_mission.sh
```

Success requires `execution_scope: live-datahub`, `repair_executed: true`,
`quality_validation_passed: true`, `active_incidents_after: 0`,
`knowledge_written_back: true`, and `knowledge_inherited_verified: true`.
Replay the captured mission in the UI; replay never repeats the mutation.

## 15. Remove the VM's setup-time public IP

After Docker images and DataHub are installed:

```bash
bash scripts/13_remove_vm_public_ip.sh
```

IAP SSH, the local UI tunnel and Cloud Run private access continue to work.

## 16. Stop and start DataHub to save credit

Stop when you are not developing or demonstrating:

```bash
bash scripts/08_stop_start.sh stop
```

Start before a demo:

```bash
bash scripts/08_stop_start.sh start
```

Wait several minutes, then check:

```bash
bash scripts/08_stop_start.sh status
```

Cloud Run scales to zero. VM CPU charges stop while the VM is stopped; disk charges continue.

## 17. Post-hackathon security cleanup

List user-managed keys:

```bash
gcloud iam service-accounts keys list \
  --iam-account="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --managed-by=user
```

Delete the temporary key by its ID:

```bash
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

Also revoke the DataHub token and delete or disable the Google API key after judging.

## Troubleshooting

### Mission Control says DEMO MODE

```bash
gcloud run services describe oncotwin-mission-control \
  --region=asia-south1 \
  --format='yaml(spec.template.spec.containers[0].env)'
```

Confirm `DEMO_MODE=false`.

### Cloud Run cannot reach DataHub

```bash
gcloud compute instances describe oncotwin-datahub \
  --zone=asia-south1-a \
  --format='get(networkInterfaces[0].networkIP)'
```

Confirm Cloud Run uses `oncotwin-net`, `oncotwin-subnet`, and the same private IP in `DATAHUB_GMS_URL`.

### MCP server cannot start

The backend image installs `uvx`. Check Cloud Run logs:

```bash
gcloud run services logs read oncotwin-mission-control --region=asia-south1 --limit=100
```

### DataHub is unhealthy

```bash
gcloud compute ssh oncotwin-datahub --zone=asia-south1-a --tunnel-through-iap \
  --command="sudo docker ps -a && sudo docker stats --no-stream"
```

If memory is exhausted, keep the VM at `e2-standard-4`; do not downsize during judging.
