#!/usr/bin/env bash
set -euo pipefail

GCP_ZONE="${GCP_ZONE:-asia-south1-a}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"
ACCESS_NAME="$(gcloud compute instances describe "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" --format='get(networkInterfaces[0].accessConfigs[0].name)')"

if [[ -z "${ACCESS_NAME}" ]]; then
  echo "The VM already has no public IP."
  exit 0
fi

gcloud compute instances delete-access-config "${DATAHUB_VM_NAME}" \
  --zone="${GCP_ZONE}" \
  --access-config-name="${ACCESS_NAME}"
echo "Public IP removed. IAP SSH and private Cloud Run access remain available."

