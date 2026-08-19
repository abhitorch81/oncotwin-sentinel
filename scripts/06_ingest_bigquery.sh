#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
: "${DATAHUB_GMS_URL:?Set DATAHUB_GMS_URL}"
: "${DATAHUB_GMS_TOKEN:?Set DATAHUB_GMS_TOKEN}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m venv "${PROJECT_ROOT}/.ingestion-venv"
"${PROJECT_ROOT}/.ingestion-venv/bin/pip" install --upgrade pip 'acryl-datahub[bigquery]'
GCP_PROJECT_ID="${GCP_PROJECT_ID}" DATAHUB_GMS_URL="${DATAHUB_GMS_URL}" DATAHUB_GMS_TOKEN="${DATAHUB_GMS_TOKEN}" \
  "${PROJECT_ROOT}/.ingestion-venv/bin/datahub" ingest -c "${PROJECT_ROOT}/ingestion/bigquery.yml"

echo "BigQuery schema, profiles, usage and available lineage were emitted to DataHub."

