#!/usr/bin/env bash
set -euo pipefail

GCP_ZONE="${GCP_ZONE:-asia-south1-a}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"

echo "Keep this terminal open, then browse to http://localhost:9002"
gcloud compute ssh "${DATAHUB_VM_NAME}" \
  --zone="${GCP_ZONE}" \
  --tunnel-through-iap \
  -- -N -L 9002:localhost:9002 -L 8088:localhost:8080

