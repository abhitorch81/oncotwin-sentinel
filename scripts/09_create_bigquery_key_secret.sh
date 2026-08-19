#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
KEY_FILE="$(mktemp)"
trap 'rm -f "${KEY_FILE}"' EXIT
SERVICE_ACCOUNT="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "Creating a narrowly permissioned service-account key because the current Analytics Agent BigQuery connector requires explicit credentials."
gcloud iam service-accounts keys create "${KEY_FILE}" --iam-account="${SERVICE_ACCOUNT}"

if gcloud secrets describe oncotwin-bigquery-credentials >/dev/null 2>&1; then
  gcloud secrets versions add oncotwin-bigquery-credentials --data-file="${KEY_FILE}" >/dev/null
else
  gcloud secrets create oncotwin-bigquery-credentials --replication-policy=automatic --data-file="${KEY_FILE}" >/dev/null
fi

echo "Credential uploaded to Secret Manager and removed from the local temporary file. Delete the service-account key after the hackathon."

