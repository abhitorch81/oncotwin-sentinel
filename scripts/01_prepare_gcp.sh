#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
GCP_REGION="${GCP_REGION:-asia-south1}"

gcloud config set project "${GCP_PROJECT_ID}"
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  vpcaccess.googleapis.com

if ! gcloud artifacts repositories describe oncotwin --location="${GCP_REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create oncotwin \
    --repository-format=docker \
    --location="${GCP_REGION}" \
    --description="OncoTwin hackathon images"
fi

if ! gcloud iam service-accounts describe "oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
  gcloud iam service-accounts create oncotwin-agent --display-name="OncoTwin Agent Runtime"
fi

if ! gcloud compute networks describe oncotwin-net >/dev/null 2>&1; then
  gcloud compute networks create oncotwin-net --subnet-mode=custom
fi

if ! gcloud compute networks subnets describe oncotwin-subnet --region="${GCP_REGION}" >/dev/null 2>&1; then
  gcloud compute networks subnets create oncotwin-subnet \
    --network=oncotwin-net \
    --region="${GCP_REGION}" \
    --range=10.42.0.0/24
fi

if ! gcloud compute firewall-rules describe oncotwin-allow-iap-ssh >/dev/null 2>&1; then
  gcloud compute firewall-rules create oncotwin-allow-iap-ssh \
    --network=oncotwin-net \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-service-accounts="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
fi

if ! gcloud compute firewall-rules describe oncotwin-allow-datahub >/dev/null 2>&1; then
  gcloud compute firewall-rules create oncotwin-allow-datahub \
    --network=oncotwin-net \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:8080 \
    --source-ranges=10.42.0.0/24 \
    --target-service-accounts="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
fi

for role_name in roles/aiplatform.user roles/bigquery.jobUser roles/bigquery.dataViewer roles/bigquery.dataEditor roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="${role_name}" >/dev/null
done

CURRENT_GCLOUD_ACCOUNT="$(gcloud config get-value account 2>/dev/null)"
if [[ "${CURRENT_GCLOUD_ACCOUNT}" == *"@"* ]]; then
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="user:${CURRENT_GCLOUD_ACCOUNT}" \
    --role="roles/iap.tunnelResourceAccessor" >/dev/null
fi

echo "Google Cloud APIs, registry and runtime identity are ready."
