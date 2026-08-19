#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
GCP_REGION="${GCP_REGION:-asia-south1}"
GCP_ZONE="${GCP_ZONE:-asia-south1-a}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/oncotwin/analytics-agent:latest"
DATAHUB_PRIVATE_IP="$(gcloud compute instances describe "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" --format='get(networkInterfaces[0].networkIP)')"

for required_secret in oncotwin-google-api-key oncotwin-bigquery-credentials oncotwin-datahub-token; do
  gcloud secrets describe "${required_secret}" >/dev/null
done

gcloud builds submit "${PROJECT_ROOT}/analytics-agent" --tag "${IMAGE_URI}"
gcloud run deploy oncotwin-analytics-agent \
  --image="${IMAGE_URI}" \
  --region="${GCP_REGION}" \
  --service-account="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --cpu=2 \
  --memory=2Gi \
  --min-instances=0 \
  --max-instances=2 \
  --timeout=300 \
  --port=8100 \
  --network=oncotwin-net \
  --subnet=oncotwin-subnet \
  --vpc-egress=private-ranges-only \
  --set-env-vars="LLM_PROVIDER=google,LLM_MODEL=gemini-2.0-flash,CHART_LLM_MODEL=gemini-1.5-flash,QUALITY_LLM_MODEL=gemini-1.5-flash,DELIGHT_LLM_MODEL=gemini-1.5-flash,DATAHUB_GMS_URL=http://${DATAHUB_PRIVATE_IP}:8080,ENGINES_CONFIG=/app/config.yaml,BIGQUERY_PROJECT=${GCP_PROJECT_ID},BIGQUERY_DATASET=oncotwin,SQL_ROW_LIMIT=500" \
  --set-secrets="GOOGLE_API_KEY=oncotwin-google-api-key:latest,DATAHUB_GMS_TOKEN=oncotwin-datahub-token:latest,BIGQUERY_CREDENTIALS_JSON=oncotwin-bigquery-credentials:latest"

ANALYTICS_URL="$(gcloud run services describe oncotwin-analytics-agent --region="${GCP_REGION}" --format='value(status.url)')"
gcloud run services update oncotwin-mission-control \
  --region="${GCP_REGION}" \
  --update-env-vars="ANALYTICS_AGENT_URL=${ANALYTICS_URL}" >/dev/null

echo "Analytics Agent: ${ANALYTICS_URL}"
