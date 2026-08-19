#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
GCP_REGION="${GCP_REGION:-asia-south1}"
GCP_ZONE="${GCP_ZONE:-asia-south1-a}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"
DATAHUB_READ_TOKEN_VERSION="${DATAHUB_READ_TOKEN_VERSION:-latest}"
DATAHUB_ADMIN_TOKEN_VERSION="${DATAHUB_ADMIN_TOKEN_VERSION:-latest}"
IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/oncotwin/mission-control:latest"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DATAHUB_PRIVATE_IP="$(gcloud compute instances describe "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" --format='get(networkInterfaces[0].networkIP)')"

gcloud builds submit "${PROJECT_ROOT}" --tag "${IMAGE_URI}"
gcloud run deploy oncotwin-mission-control \
  --image="${IMAGE_URI}" \
  --region="${GCP_REGION}" \
  --platform=managed \
  --service-account="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --cpu=2 \
  --memory=2Gi \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300 \
  --network=oncotwin-net \
  --subnet=oncotwin-subnet \
  --vpc-egress=private-ranges-only \
  --set-env-vars="APP_ENV=production,DEMO_MODE=false,DATAHUB_GMS_URL=http://${DATAHUB_PRIVATE_IP}:8080,DATAHUB_MCP_COMMAND=uvx,DATAHUB_MCP_PACKAGE=mcp-server-datahub@latest,TOOLS_IS_MUTATION_ENABLED=true,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${GCP_PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,BIGQUERY_LOCATION=${GCP_REGION},GEMINI_MODEL=gemini-2.5-flash,MISSION_STORE_PATH=/tmp/oncotwin-missions" \
  --set-secrets="DATAHUB_GMS_TOKEN=oncotwin-datahub-token:${DATAHUB_READ_TOKEN_VERSION},DATAHUB_ADMIN_TOKEN=oncotwin-datahub-token:${DATAHUB_ADMIN_TOKEN_VERSION},WRITEBACK_APPROVAL_SECRET=oncotwin-writeback-approval:latest"

gcloud run services describe oncotwin-mission-control --region="${GCP_REGION}" --format='value(status.url)'
