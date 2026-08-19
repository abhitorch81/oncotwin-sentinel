#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
GCP_REGION="${GCP_REGION:-asia-south1}"
GCP_REPOSITORY="${GCP_REPOSITORY:-oncotwin}"

gcloud config set project "${GOOGLE_CLOUD_PROJECT}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com logging.googleapis.com
gcloud artifacts repositories describe "${GCP_REPOSITORY}" --location "${GCP_REGION}" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "${GCP_REPOSITORY}" --repository-format=docker --location "${GCP_REGION}"

API_IMAGE="${GCP_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${GCP_REPOSITORY}/api:milestone-1"
WEB_IMAGE="${GCP_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${GCP_REPOSITORY}/web:milestone-1"

gcloud builds submit --config infra/gcp/cloudbuild-api.yaml --substitutions="_IMAGE=${API_IMAGE}" .
gcloud run deploy oncotwin-agentic-api --image "${API_IMAGE}" --region "${GCP_REGION}" --allow-unauthenticated \
  --set-env-vars="DEMO_MODE=true,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
API_URL="$(gcloud run services describe oncotwin-agentic-api --region "${GCP_REGION}" --format='value(status.url)')"

gcloud builds submit --config infra/gcp/cloudbuild-web.yaml \
  --substitutions="_IMAGE=${WEB_IMAGE},_VITE_API_URL=${API_URL}" .
gcloud run deploy oncotwin-agentic-web --image "${WEB_IMAGE}" --region "${GCP_REGION}" --allow-unauthenticated
WEB_URL="$(gcloud run services describe oncotwin-agentic-web --region "${GCP_REGION}" --format='value(status.url)')"
gcloud run services update oncotwin-agentic-api --region "${GCP_REGION}" --update-env-vars="ALLOWED_ORIGINS=${WEB_URL}"

echo "API: ${API_URL}"
echo "Web: ${WEB_URL}"
