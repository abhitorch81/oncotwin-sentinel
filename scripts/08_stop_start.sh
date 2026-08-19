#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
GCP_ZONE="${GCP_ZONE:-asia-south1-a}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"

case "${ACTION}" in
  start) gcloud compute instances start "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" ;;
  stop) gcloud compute instances stop "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" ;;
  status) gcloud compute instances describe "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" --format='get(status)' ;;
  *) echo "Usage: $0 start|stop|status" >&2; exit 2 ;;
esac

