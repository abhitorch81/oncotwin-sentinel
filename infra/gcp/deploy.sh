#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"

GCP_REGION="${GCP_REGION:-asia-south1}"
GCP_REPOSITORY="${GCP_REPOSITORY:-oncotwin}"
API_SERVICE="${API_SERVICE:-oncotwin-agentic-api}"
WEB_SERVICE="${WEB_SERVICE:-oncotwin-agentic-web}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-oncotwin-runtime}"
RELEASE_TAG="${RELEASE_TAG:-$(git rev-parse --short HEAD)}"
GEMINI_MODEL_ID="${GEMINI_MODEL_ID:-gemini-3.5-flash}"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"

gcloud config set project "${GOOGLE_CLOUD_PROJECT}"

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  iam.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com

if ! gcloud iam service-accounts describe "${RUNTIME_SA}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${RUNTIME_SA_NAME}" \
    --display-name="OncoTwin Cloud Run runtime"
fi

for role in roles/datastore.user roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding "${GOOGLE_CLOUD_PROJECT}" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="${role}" \
    --condition=None \
    --quiet >/dev/null
done

if ! gcloud artifacts repositories describe "${GCP_REPOSITORY}" \
  --location="${GCP_REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${GCP_REPOSITORY}" \
    --repository-format=docker \
    --location="${GCP_REGION}"
fi

API_IMAGE="${GCP_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${GCP_REPOSITORY}/api:${RELEASE_TAG}"
WEB_IMAGE="${GCP_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${GCP_REPOSITORY}/web:${RELEASE_TAG}"

gcloud builds submit \
  --config=infra/gcp/cloudbuild-api.yaml \
  --substitutions="_IMAGE=${API_IMAGE}" \
  .

gcloud run deploy "${API_SERVICE}" \
  --image="${API_IMAGE}" \
  --region="${GCP_REGION}" \
  --service-account="${RUNTIME_SA}" \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=1Gi \
  --concurrency=20 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300s \
  --deploy-health-check \
  --startup-probe="initialDelaySeconds=0,timeoutSeconds=3,periodSeconds=5,failureThreshold=12,httpGet.port=8080,httpGet.path=/api/health" \
  --liveness-probe="initialDelaySeconds=10,timeoutSeconds=3,periodSeconds=30,failureThreshold=3,httpGet.port=8080,httpGet.path=/api/health" \
  --set-env-vars="APP_ENV=production,DEMO_MODE=false,FIRESTORE_ENABLED=true,FIRESTORE_DATABASE=(default),GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=${GEMINI_MODEL_ID},ADK_ENABLED=true,ADK_MODEL=${GEMINI_MODEL_ID},ALLOWED_ORIGINS=https://pending.invalid"

API_URL="$(gcloud run services describe "${API_SERVICE}" \
  --region="${GCP_REGION}" --format='value(status.url)')"

gcloud builds submit \
  --config=infra/gcp/cloudbuild-web.yaml \
  --substitutions="_IMAGE=${WEB_IMAGE},_VITE_API_URL=${API_URL}" \
  .

gcloud run deploy "${WEB_SERVICE}" \
  --image="${WEB_IMAGE}" \
  --region="${GCP_REGION}" \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=3 \
  --deploy-health-check \
  --startup-probe="initialDelaySeconds=0,timeoutSeconds=3,periodSeconds=5,failureThreshold=12,httpGet.port=8080,httpGet.path=/health" \
  --liveness-probe="initialDelaySeconds=10,timeoutSeconds=3,periodSeconds=30,failureThreshold=3,httpGet.port=8080,httpGet.path=/health"

WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" \
  --region="${GCP_REGION}" --format='value(status.url)')"

gcloud run services update "${API_SERVICE}" \
  --region="${GCP_REGION}" \
  --update-env-vars="ALLOWED_ORIGINS=${WEB_URL}" >/dev/null

API_URL="$(gcloud run services describe "${API_SERVICE}" \
  --region="${GCP_REGION}" --format='value(status.url)')"

HEALTH_JSON="$(curl --fail --silent --show-error "${API_URL}/api/health")"
MEMORY_JSON="$(curl --fail --silent --show-error "${API_URL}/api/memory/proof")"
ELIGIBILITY_JSON="$(curl --fail --silent --show-error "${API_URL}/api/eligibility/proof")"
curl --fail --silent --show-error "${WEB_URL}/health" >/dev/null

python3 - "${HEALTH_JSON}" "${MEMORY_JSON}" "${ELIGIBILITY_JSON}" "${GEMINI_MODEL_ID}" <<'PY'
import json
import sys

health = json.loads(sys.argv[1])
memory = json.loads(sys.argv[2])
eligibility = json.loads(sys.argv[3])
expected_model = sys.argv[4]

assert health.get("ok") is True, health
assert health.get("adk_enabled") is True, health
assert health.get("gemini_model") == expected_model, health
assert health.get("gemini_access") == "vertex_ai", health
assert health.get("minimum_gemini_version_met") is True, health
assert health.get("memory_backend_configured") == "firestore", health
assert memory.get("active_backend") == "firestore", memory
assert memory.get("persistent") is True, memory
assert memory.get("healthy") is True, memory
assert memory.get("degraded") is False, memory
assert eligibility.get("requirements_met") is True, eligibility
assert eligibility.get("gemini", {}).get("model") == expected_model, eligibility
assert eligibility.get("agent_framework", {}).get("name") == "Google ADK", eligibility
assert eligibility.get("google_cloud_infrastructure", {}).get("configured") is True, eligibility
print(json.dumps({"health": health, "memory": memory, "eligibility": eligibility}, indent=2))
PY

echo "API: ${API_URL}"
echo "Web: ${WEB_URL}"
echo "Release: ${RELEASE_TAG}"
