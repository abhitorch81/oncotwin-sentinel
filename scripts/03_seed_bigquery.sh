#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/../data/bigquery_demo.sql"
TMP_SQL="$(mktemp)"
trap 'rm -f "${TMP_SQL}"' EXIT

sed "s/PROJECT_ID/${GCP_PROJECT_ID}/g" "${SQL_FILE}" > "${TMP_SQL}"
bq query --location=asia-south1 --use_legacy_sql=false < "${TMP_SQL}"
echo "Created de-identified OncoTwin BigQuery demonstration tables."

