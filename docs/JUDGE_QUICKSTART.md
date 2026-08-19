# Judge Quickstart

This guide proves the submission without requiring a judge to understand every implementation detail.

## Fastest evaluation: hosted application

1. Open the Cloud Run URL supplied in the Devpost entry.
2. Confirm the header reads **DATAHUB LIVE · V10.1.0**.
3. Open **Proof Galaxy**.
4. Select each of the seven mission worlds and click **Capture fresh proof**.
5. Confirm the selected world shows its condition-specific BigQuery URN and `6/6` successful MCP reads.
6. Open **Live Mission**, select **Biomarker Completeness Crisis**, and click **Run selected mission**.
7. Inspect Context Scout, Lineage Sentinel, ML Guardian, Repair Engineer and Governance Steward.
8. Confirm the workflow stops at **Approval Required** rather than mutating automatically.

## Flagship governed-writeback proof

Before approval, capture:

- active incident on `progression_features`
- downstream lineage to `progression_scores`
- ML Guardian block decision
- schema-grounded SQL

After the operator enters the approval secret, capture:

- BigQuery repair and validation job IDs
- zero NULL signal rows and `PASS`
- resolved DataHub incident
- `AgentRepaired` tag
- responsible agent and UTC timestamp
- repair/validation job IDs in DataHub custom properties
- SHA-256 receipt
- MCP read-after-write verification

## Machine-readable proof

```bash
export APP_URL="THE_CLOUD_RUN_URL"

bash scripts/18_verify_all_datahub_conditions.sh
```

Expected:

```text
status: PASS
datahub_native_conditions: 7/7
reads: 6/6 for every condition
```

The approval-gated proof additionally requires the locally held approval value:

```bash
export WRITEBACK_APPROVAL_SECRET="$(gcloud secrets versions access latest \
  --secret=oncotwin-writeback-approval \
  --project="${GCP_PROJECT_ID}")"

bash scripts/16_verify_live_rl_mission.sh
unset WRITEBACK_APPROVAL_SECRET
```

## Local no-cloud evaluation

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/oncotwin-datahub.git
cd oncotwin-datahub
chmod +x scripts/*.sh
bash scripts/12_local_demo.sh
```

Open <http://localhost:8080>. The application clearly displays `DEMO MODE`; external DataHub and GCP writes are simulated.

## What is live and what is simulated?

| Capability | Hosted live mode |
|---|---|
| DataHub identity, schema, owners, tags, queries and lineage | Live |
| Six MCP reads per condition | Live |
| BigQuery failure, repair and validation jobs | Live for flagship mission |
| DataHub incident creation and resolution | Live, approval governed |
| DataHub description/tag/custom-property writeback | Live for flagship mission |
| Biological progression and counterfactual response | Synthetic research simulation |
| Protein conformation visualization | Schematic; not a structure predictor |
| Clinical diagnosis or treatment advice | Never provided |

## Repository navigation

- `README.md` — project and full deployment
- `ONCOTWIN_C4_ARCHITECTURE_V10_1.md` — architecture
- `DEPLOYMENT.md` — detailed GCP commands and troubleshooting
- `DEMO_RUNBOOK.md` — five-minute presentation
- `scripts/16_verify_live_rl_mission.sh` — end-to-end mutation proof
- `scripts/18_verify_all_datahub_conditions.sh` — 7/7 read proof

