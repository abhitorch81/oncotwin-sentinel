#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
: "${DATAHUB_GMS_TOKEN:?Set DATAHUB_GMS_TOKEN locally; it will not be printed}"

create_or_update_secret() {
  local secret_name="$1" secret_value="$2"
  if gcloud secrets describe "${secret_name}" >/dev/null 2>&1; then
    printf '%s' "${secret_value}" | gcloud secrets versions add "${secret_name}" --data-file=- >/dev/null
  else
    printf '%s' "${secret_value}" | gcloud secrets create "${secret_name}" --replication-policy=automatic --data-file=- >/dev/null
  fi
}

APPROVAL_SECRET="${WRITEBACK_APPROVAL_SECRET:-$(openssl rand -hex 24)}"
create_or_update_secret oncotwin-datahub-token "${DATAHUB_GMS_TOKEN}"
create_or_update_secret oncotwin-writeback-approval "${APPROVAL_SECRET}"

if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
  create_or_update_secret oncotwin-google-api-key "${GOOGLE_API_KEY}"
fi

echo "Secrets stored. Save the writeback approval secret securely if it was generated during this run."

