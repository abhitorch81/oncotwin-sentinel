#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAMBDA_DIR="${PROJECT_ROOT}/aws/lambda_memory_vectorizer"
AWS_REGION="${AWS_REGION:-ap-south-1}"
FUNCTION_NAME="${FUNCTION_NAME:-oncotwin-memory-vectorizer}"
ECR_REPOSITORY="${ECR_REPOSITORY:-oncotwin-memory-vectorizer}"
ROLE_NAME="${ROLE_NAME:-oncotwin-memory-vectorizer-role}"
SECRET_NAME="${SECRET_NAME:-oncotwin/memory-vectorizer}"
MEMORY_TENANT_ID="${MEMORY_TENANT_ID:-11111111-1111-1111-1111-111111111111}"

for command_name in aws docker python3 openssl; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    echo "Missing required command: ${command_name}" >&2
    exit 1
  }
done

echo "This deploys paid-capable AWS resources: ECR, Secrets Manager, CloudWatch Logs, and Lambda."
read -r -p "Continue in ${AWS_REGION}? [y/N]: " REPLY
[[ "${REPLY}" == "y" || "${REPLY}" == "Y" ]] || exit 0

CALLER_ARN="$(aws sts get-caller-identity --query Arn --output text)"
if [[ "${CALLER_ARN}" == *":root" ]]; then
  echo "Warning: deploying as root. Create a least-privilege deployment identity after the demo."
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  read -r -s -p "Paste the current CockroachDB URL: " DATABASE_URL
  echo
fi
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  read -r -s -p "Paste the Gemini API key: " GEMINI_API_KEY
  echo
fi
if [[ -z "${MEMORY_VECTORIZER_TOKEN:-}" ]]; then
  MEMORY_VECTORIZER_TOKEN="$(openssl rand -hex 32)"
fi

[[ -n "${DATABASE_URL}" && -n "${GEMINI_API_KEY}" ]] || {
  echo "DATABASE_URL and GEMINI_API_KEY are required." >&2
  exit 1
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT
chmod 700 "${TMP_DIR}"
export DATABASE_URL GEMINI_API_KEY MEMORY_VECTORIZER_TOKEN MEMORY_TENANT_ID
python3 - "${TMP_DIR}/secret.json" <<'PY'
import json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
path.write_text(json.dumps({
    "database_url": os.environ["DATABASE_URL"],
    "gemini_api_key": os.environ["GEMINI_API_KEY"],
    "shared_token": os.environ["MEMORY_VECTORIZER_TOKEN"],
    "tenant_id": os.environ["MEMORY_TENANT_ID"],
}), encoding="utf-8")
path.chmod(0o600)
PY

if aws secretsmanager describe-secret --region "${AWS_REGION}" --secret-id "${SECRET_NAME}" >/dev/null 2>&1; then
  SECRET_ARN="$(aws secretsmanager put-secret-value \
    --region "${AWS_REGION}" --secret-id "${SECRET_NAME}" \
    --secret-string "file://${TMP_DIR}/secret.json" --query ARN --output text)"
else
  SECRET_ARN="$(aws secretsmanager create-secret \
    --region "${AWS_REGION}" --name "${SECRET_NAME}" \
    --description "OncoTwin synthetic research memory vectorizer" \
    --secret-string "file://${TMP_DIR}/secret.json" --query ARN --output text)"
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
aws ecr describe-repositories --region "${AWS_REGION}" --repository-names "${ECR_REPOSITORY}" >/dev/null 2>&1 || \
  aws ecr create-repository --region "${AWS_REGION}" --repository-name "${ECR_REPOSITORY}" \
    --image-scanning-configuration scanOnPush=true >/dev/null

aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
docker buildx build --platform linux/arm64 --provenance=false --load \
  -t "${ECR_URI}:latest" "${LAMBDA_DIR}"
docker push "${ECR_URI}:latest"

python3 - "${TMP_DIR}/trust.json" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}), encoding="utf-8")
PY

if ! aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${ROLE_NAME}" \
    --assume-role-policy-document "file://${TMP_DIR}/trust.json" >/dev/null
fi
ROLE_ARN="$(aws iam get-role --role-name "${ROLE_NAME}" --query Role.Arn --output text)"

export SECRET_ARN AWS_REGION ACCOUNT_ID
python3 - "${TMP_DIR}/permissions.json" <<'PY'
import json, os, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": f"arn:aws:logs:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_ID']}:log-group:/aws/lambda/*"
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": os.environ["SECRET_ARN"]
    }
  ]
}), encoding="utf-8")
PY
aws iam put-role-policy --role-name "${ROLE_NAME}" \
  --policy-name oncotwin-memory-vectorizer-runtime \
  --policy-document "file://${TMP_DIR}/permissions.json"

if aws lambda get-function --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" >/dev/null 2>&1; then
  aws lambda update-function-code --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
    --image-uri "${ECR_URI}:latest" >/dev/null
  aws lambda wait function-updated --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}"
  aws lambda update-function-configuration --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
    --role "${ROLE_ARN}" --timeout 45 --memory-size 1024 \
    --environment "Variables={MEMORY_SECRET_ARN=${SECRET_ARN}}" >/dev/null
else
  echo "Waiting briefly for the new Lambda role to propagate..."
  sleep 10
  aws lambda create-function --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
    --package-type Image --code "ImageUri=${ECR_URI}:latest" --role "${ROLE_ARN}" \
    --architectures arm64 --timeout 45 --memory-size 1024 \
    --environment "Variables={MEMORY_SECRET_ARN=${SECRET_ARN}}" >/dev/null
fi
aws lambda wait function-active-v2 --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}"

if ! aws lambda get-function-url-config --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" >/dev/null 2>&1; then
  aws lambda create-function-url-config --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
    --auth-type NONE >/dev/null
fi

aws lambda add-permission --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
  --statement-id FunctionURLAllowPublicAccess --action lambda:InvokeFunctionUrl \
  --principal '*' --function-url-auth-type NONE >/dev/null 2>&1 || true
aws lambda add-permission --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" \
  --statement-id FunctionURLInvokeFunction --action lambda:InvokeFunction \
  --principal '*' --invoked-via-function-url >/dev/null 2>&1 || true

FUNCTION_URL="$(aws lambda get-function-url-config --region "${AWS_REGION}" \
  --function-name "${FUNCTION_NAME}" --query FunctionUrl --output text)"

ENV_FILE="${PROJECT_ROOT}/.env.memorymesh.local"
umask 077
{
  printf 'MEMORY_VECTORIZER_URL=%s\n' "${FUNCTION_URL}"
  printf 'MEMORY_VECTORIZER_TOKEN=%s\n' "${MEMORY_VECTORIZER_TOKEN}"
} > "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

echo "AWS Lambda memory vectorizer deployed."
echo "Function URL: ${FUNCTION_URL}"
echo "Local backend settings saved to .env.memorymesh.local (mode 600; do not commit)."
echo "Testing Lambda health..."
curl -fsS -X POST "${FUNCTION_URL}" \
  -H "Content-Type: application/json" \
  -H "X-OncoTwin-Token: ${MEMORY_VECTORIZER_TOKEN}" \
  -d '{"action":"health"}' | python3 -m json.tool
