#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
: "${DATAHUB_GMS_URL:?Set DATAHUB_GMS_URL}"
: "${DATAHUB_GMS_TOKEN:?Set DATAHUB_GMS_TOKEN}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PROJECT_ROOT}/.ingestion-venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Run scripts/06_ingest_bigquery.sh first so the isolated DataHub SDK environment exists." >&2
  exit 1
fi

"${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/17_bootstrap_datahub_context.py"
