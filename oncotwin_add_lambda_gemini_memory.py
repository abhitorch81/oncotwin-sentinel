#!/usr/bin/env python3
"""Add an AWS Lambda + Google Gemini vector worker to OncoTwin MemoryMesh.

Run from the OncoTwin repository root:
    python3 oncotwin_add_lambda_gemini_memory.py

The installer is idempotent, does not read or print secrets, and backs up every
existing file that it changes. The generated deployment script requires an
explicit confirmation before it creates AWS resources.
"""

from __future__ import annotations

import argparse
import compileall
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


MARKER = "# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors"


BACKEND_CLIENT = r'''# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class VectorizerError(RuntimeError):
    """Raised when the AWS Lambda memory worker cannot complete a request."""


def invoke_memory_vectorizer(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.memory_vectorizer_url or not settings.memory_vectorizer_token:
        raise VectorizerError("Memory vectorizer is not configured")

    request_body = {"action": action, **payload}
    try:
        response = httpx.post(
            settings.memory_vectorizer_url,
            headers={
                "X-OncoTwin-Token": settings.memory_vectorizer_token,
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=settings.memory_vectorizer_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise VectorizerError("Memory vectorizer request failed") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise VectorizerError("Memory vectorizer returned a non-JSON response") from exc

    if response.status_code >= 400:
        message = result.get("error", "Memory vectorizer rejected the request")
        raise VectorizerError(str(message))
    return result
'''


LAMBDA_HANDLER = r'''# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from functools import lru_cache
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

import boto3
import certifi
import psycopg
from google import genai
from google.genai import types


MODEL_ID = "gemini-embedding-001"
VECTOR_DIMENSIONS = 1024


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body, default=str, separators=(",", ":")),
    }


@lru_cache(maxsize=1)
def _settings() -> dict[str, str]:
    secret_arn = os.environ.get("MEMORY_SECRET_ARN", "")
    if not secret_arn:
        raise RuntimeError("MEMORY_SECRET_ARN is not configured")
    value = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    settings = json.loads(value["SecretString"])
    required = ("database_url", "gemini_api_key", "shared_token", "tenant_id")
    missing = [name for name in required if not settings.get(name)]
    if missing:
        raise RuntimeError("Memory secret is missing required fields")
    return settings


def _database_url(raw_url: str) -> str:
    if raw_url.startswith("cockroachdb://"):
        raw_url = "postgresql://" + raw_url[len("cockroachdb://"):]
    parts = urlsplit(raw_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["sslmode"] = "verify-full"
    query["sslrootcert"] = certifi.where()
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def _authorized(event: dict[str, Any], expected: str) -> bool:
    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    supplied = headers.get("x-oncotwin-token", "")
    return bool(supplied) and hmac.compare_digest(supplied, expected)


def _uuid(value: Any, field_name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a UUID") from exc


def _embedding(text_value: str, title: str | None, task_type: str, api_key: str) -> list[float]:
    text_value = text_value.strip()
    if not text_value:
        raise ValueError("Embedding text cannot be empty")
    if len(text_value) > 50_000:
        raise ValueError("Embedding text exceeds 50,000 characters")

    config = types.EmbedContentConfig(
        output_dimensionality=VECTOR_DIMENSIONS,
        task_type=task_type,
        title=title if task_type == "RETRIEVAL_DOCUMENT" else None,
    )
    result = genai.Client(api_key=api_key).models.embed_content(
        model=MODEL_ID,
        contents=text_value,
        config=config,
    )
    values = list(result.embeddings[0].values)
    if len(values) != VECTOR_DIMENSIONS:
        raise RuntimeError(f"Expected {VECTOR_DIMENSIONS} dimensions, received {len(values)}")
    return values


def _research_only(metadata: Any) -> bool:
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    return isinstance(metadata, dict) and metadata.get("research_only") is True


def _health(connection: psycopg.Connection[Any]) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), version()")
        database_name, version = cursor.fetchone()
        cursor.execute(
            "SELECT count(*) FROM pg_indexes WHERE tablename = 'agent_memories' "
            "AND indexname = 'agent_memories_embedding_idx'"
        )
        index_count = cursor.fetchone()[0]
    return {
        "ok": True,
        "aws_service": "AWS Lambda",
        "embedding_provider": "Google Gemini",
        "embedding_model": MODEL_ID,
        "dimensions": VECTOR_DIMENSIONS,
        "database": database_name,
        "cockroach_version": version,
        "vector_index_ready": int(index_count) == 1,
    }


def _embed_memory(
    connection: psycopg.Connection[Any], body: dict[str, Any], settings: dict[str, str]
) -> dict[str, Any]:
    memory_id = _uuid(body.get("memory_id"), "memory_id")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT am.memory_id, am.title, am.content, p.synthetic_code, p.metadata "
            "FROM agent_memories AS am JOIN patients AS p "
            "ON p.tenant_id = am.tenant_id AND p.patient_id = am.patient_id "
            "WHERE am.tenant_id = %s::UUID AND am.memory_id = %s::UUID",
            (settings["tenant_id"], memory_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise LookupError("Memory not found")
        _, title, content, synthetic_code, patient_metadata = row
        if not _research_only(patient_metadata):
            raise PermissionError("Only synthetic research memories may be embedded")

        values = _embedding(content, title, "RETRIEVAL_DOCUMENT", settings["gemini_api_key"])
        vector_literal = json.dumps(values, separators=(",", ":"))
        cursor.execute(
            "UPDATE agent_memories SET embedding = CAST(%s AS VECTOR) "
            "WHERE tenant_id = %s::UUID AND memory_id = %s::UUID RETURNING memory_id",
            (vector_literal, settings["tenant_id"], memory_id),
        )
        updated = cursor.fetchone()
    connection.commit()
    if updated is None:
        raise RuntimeError("Memory embedding update failed")
    return {
        "ok": True,
        "action": "embed_memory",
        "aws_service": "AWS Lambda",
        "embedding_provider": "Google Gemini",
        "embedding_model": MODEL_ID,
        "dimensions": len(values),
        "memory_id": memory_id,
        "synthetic_code": synthetic_code,
        "embedding_sha256": hashlib.sha256(vector_literal.encode("utf-8")).hexdigest(),
        "stored_in": "CockroachDB distributed vector index",
    }


def _semantic_search(
    connection: psycopg.Connection[Any], body: dict[str, Any], settings: dict[str, str]
) -> dict[str, Any]:
    synthetic_code = str(body.get("synthetic_code", "")).strip().upper()
    query = str(body.get("query", "")).strip()
    limit = max(1, min(int(body.get("limit", 5)), 20))
    if not synthetic_code:
        raise ValueError("synthetic_code is required")

    values = _embedding(query, None, "RETRIEVAL_QUERY", settings["gemini_api_key"])
    vector_literal = json.dumps(values, separators=(",", ":"))
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT p.metadata FROM patients AS p "
            "WHERE p.tenant_id = %s::UUID AND p.synthetic_code = %s",
            (settings["tenant_id"], synthetic_code),
        )
        patient = cursor.fetchone()
        if patient is None:
            raise LookupError("Synthetic patient not found")
        if not _research_only(patient[0]):
            raise PermissionError("Only synthetic research memories may be searched")

        cursor.execute(
            "SELECT am.memory_id, am.title, am.content, am.memory_type, am.metadata, "
            "am.confidence, am.source_agent, "
            "1 - (am.embedding <=> CAST(%s AS VECTOR)) AS similarity "
            "FROM agent_memories AS am JOIN patients AS p "
            "ON p.tenant_id = am.tenant_id AND p.patient_id = am.patient_id "
            "WHERE am.tenant_id = %s::UUID AND p.synthetic_code = %s "
            "AND am.embedding IS NOT NULL ORDER BY similarity DESC LIMIT %s",
            (vector_literal, settings["tenant_id"], synthetic_code, limit),
        )
        columns = [item.name for item in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    for row in rows:
        row["memory_id"] = str(row["memory_id"])
        row["similarity"] = float(row["similarity"])
        row["confidence"] = float(row["confidence"]) if row["confidence"] is not None else None
    return {
        "ok": True,
        "action": "semantic_search",
        "aws_service": "AWS Lambda",
        "embedding_provider": "Google Gemini",
        "embedding_model": MODEL_ID,
        "dimensions": len(values),
        "synthetic_code": synthetic_code,
        "query": query,
        "matches": rows,
        "match_count": len(rows),
        "searched_in": "CockroachDB distributed vector index",
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    try:
        settings = _settings()
        if not _authorized(event, settings["shared_token"]):
            return _response(401, {"ok": False, "error": "Unauthorized"})
        body = _body(event)
        action = str(body.get("action", "")).strip()
        with psycopg.connect(_database_url(settings["database_url"]), connect_timeout=10) as connection:
            if action == "health":
                result = _health(connection)
            elif action == "embed_memory":
                result = _embed_memory(connection, body, settings)
            elif action == "semantic_search":
                result = _semantic_search(connection, body, settings)
            else:
                return _response(400, {"ok": False, "error": "Unsupported action"})
        return _response(200, result)
    except ValueError as exc:
        return _response(400, {"ok": False, "error": str(exc)})
    except LookupError as exc:
        return _response(404, {"ok": False, "error": str(exc)})
    except PermissionError as exc:
        return _response(403, {"ok": False, "error": str(exc)})
    except Exception as exc:
        print(json.dumps({"level": "ERROR", "error_type": type(exc).__name__}))
        return _response(500, {"ok": False, "error": "Memory vectorizer failed"})
'''


LAMBDA_DOCKERFILE = r'''FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
COPY handler.py ${LAMBDA_TASK_ROOT}/handler.py

CMD ["handler.lambda_handler"]
'''


LAMBDA_REQUIREMENTS = '''google-genai>=1.20,<2
psycopg[binary]>=3.2,<4
certifi>=2025.1
'''


DEPLOY_SCRIPT = r'''#!/usr/bin/env bash
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
'''


README = r'''# OncoTwin MemoryMesh: Gemini + AWS Lambda

This extension removes Amazon Bedrock from the critical path while preserving a
meaningful AWS deployment:

1. The FastAPI API requests an embedding or semantic search.
2. An AWS Lambda container executes the memory workflow.
3. Google Gemini `gemini-embedding-001` generates a 1024-dimensional vector.
4. Lambda writes/searches that vector in CockroachDB's distributed vector index.

Only synthetic, research-only patient records are accepted by the Lambda worker.

## 1. Apply the installer

From the repository root:

```bash
python3 oncotwin_add_lambda_gemini_memory.py
python -m pip install -r requirements.txt
```

## 2. Deploy the worker

Docker Desktop must be running. Ensure `DATABASE_URL` and `GEMINI_API_KEY` are
available in the shell, or the script will prompt for them without echoing.

```bash
bash scripts/deploy_lambda_memory_vectorizer.sh
```

The deployment creates paid-capable AWS resources only after an explicit `y`
confirmation: ECR, Lambda, Secrets Manager, and CloudWatch Logs. It creates
`.env.memorymesh.local` with mode 600. Never commit that file.

## 3. Run the backend

```bash
set -a
source .env.memorymesh.local
set +a
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep `DATABASE_URL` configured in the backend shell as before.

## 4. Verify the integration

```bash
curl -s -X POST http://127.0.0.1:8000/api/memory/vectorizer/health | python3 -m json.tool

curl -s -X POST \
  http://127.0.0.1:8000/api/memory/memories/30000000-0000-0000-0000-000000000001/embed \
  | python3 -m json.tool

curl -s -X POST \
  http://127.0.0.1:8000/api/memory/patients/ONCO-007/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"What resistance mechanism is emerging?","limit":5}' \
  | python3 -m json.tool

curl -s http://127.0.0.1:8000/api/memory/patients/ONCO-007 | python3 -m json.tool
```

The final patient response should show `"embedded": true`.

## Security notes

- Do not use real patient data. The worker rejects records without
  `metadata.research_only=true`.
- The Function URL is protected by a high-entropy application token. Rotate it
  before a public demo if it is exposed.
- Database and Gemini credentials are stored in AWS Secrets Manager, not in the
  Lambda image.
- Replace root deployment access with a least-privilege IAM deployment identity.
'''


ROUTES_APPEND = r'''


# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
class SemanticMemorySearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/api/memory/vectorizer/health")
def memory_vectorizer_health() -> dict[str, Any]:
    try:
        return invoke_memory_vectorizer("health", {})
    except VectorizerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/memory/memories/{memory_id}/embed")
def embed_agent_memory(memory_id: str) -> dict[str, Any]:
    try:
        return invoke_memory_vectorizer("embed_memory", {"memory_id": memory_id})
    except VectorizerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/memory/patients/{synthetic_code}/search")
def semantic_memory_search(
    synthetic_code: str, request: SemanticMemorySearchRequest
) -> dict[str, Any]:
    try:
        return invoke_memory_vectorizer(
            "semantic_search",
            {
                "synthetic_code": synthetic_code.upper(),
                "query": request.query,
                "limit": request.limit,
            },
        )
    except VectorizerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
'''


def patch_once(content: str, anchor: str, replacement: str, file_name: str) -> str:
    if replacement in content:
        return content
    if anchor not in content:
        raise RuntimeError(f"Required anchor not found in {file_name}: {anchor!r}")
    return content.replace(anchor, replacement, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="OncoTwin repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_py = root / "backend/app/config.py"
    routes_py = root / "backend/app/memory_routes.py"
    requirements = root / "requirements.txt"
    for path in (config_py, routes_py, requirements):
        if not path.is_file():
            raise SystemExit(
                "Run the CockroachDB memory patch first; missing " + str(path.relative_to(root))
            )

    config_content = config_py.read_text(encoding="utf-8")
    routes_content = routes_py.read_text(encoding="utf-8")
    req_content = requirements.read_text(encoding="utf-8")

    config_marker = "    # OncoTwin MemoryMesh: AWS Lambda + Gemini vectors\n"
    if config_marker not in config_content:
        anchor = '    memory_tenant_id: str = "11111111-1111-1111-1111-111111111111"\n'
        addition = (
            anchor
            + "\n"
            + config_marker
            + '    memory_vectorizer_url: str = ""\n'
            + '    memory_vectorizer_token: str = ""\n'
            + "    memory_vectorizer_timeout_seconds: float = 60.0\n"
        )
        config_content = patch_once(config_content, anchor, addition, "backend/app/config.py")

    routes_content = patch_once(
        routes_content,
        "from typing import Any\n",
        "from typing import Any\n\nfrom pydantic import BaseModel, Field\n",
        "backend/app/memory_routes.py",
    )
    routes_content = patch_once(
        routes_content,
        "from .memory_repository import patient_memory_bundle\n",
        "from .memory_repository import patient_memory_bundle\n"
        "from .lambda_vectorizer import VectorizerError, invoke_memory_vectorizer\n",
        "backend/app/memory_routes.py",
    )
    if MARKER not in routes_content:
        routes_content = routes_content.rstrip() + "\n" + ROUTES_APPEND.lstrip()

    dependency = "google-genai>=1.20,<2"
    existing_names = {
        re.split(r"[<>=!~]", line, maxsplit=1)[0].strip().lower()
        for line in req_content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if "google-genai" not in existing_names:
        req_content = req_content.rstrip() + "\n" + dependency + "\n"

    backend_client_path = root / "backend/app/lambda_vectorizer.py"
    lambda_dir = root / "aws/lambda_memory_vectorizer"
    lambda_handler_path = lambda_dir / "handler.py"
    lambda_dockerfile_path = lambda_dir / "Dockerfile"
    lambda_requirements_path = lambda_dir / "requirements.txt"
    deploy_path = root / "scripts/deploy_lambda_memory_vectorizer.sh"
    readme_path = root / "AWS_LAMBDA_MEMORY.md"
    gitignore = root / ".gitignore"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = root / f".lambda-gemini-backup-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    changed_paths = (
        config_py,
        routes_py,
        requirements,
        backend_client_path,
        lambda_handler_path,
        lambda_dockerfile_path,
        lambda_requirements_path,
        deploy_path,
        readme_path,
        gitignore,
    )
    for path in changed_paths:
        if not path.exists():
            continue
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    config_py.write_text(config_content, encoding="utf-8")
    routes_py.write_text(routes_content, encoding="utf-8")
    requirements.write_text(req_content, encoding="utf-8")
    backend_client_path.write_text(BACKEND_CLIENT, encoding="utf-8")

    lambda_dir.mkdir(parents=True, exist_ok=True)
    lambda_handler_path.write_text(LAMBDA_HANDLER, encoding="utf-8")
    lambda_dockerfile_path.write_text(LAMBDA_DOCKERFILE, encoding="utf-8")
    lambda_requirements_path.write_text(LAMBDA_REQUIREMENTS, encoding="utf-8")

    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    deploy_path.write_text(DEPLOY_SCRIPT, encoding="utf-8")
    deploy_path.chmod(0o755)
    readme_path.write_text(README, encoding="utf-8")

    gitignore_content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ".env.memorymesh.local" not in gitignore_content.splitlines():
        gitignore.write_text(gitignore_content.rstrip() + "\n.env.memorymesh.local\n", encoding="utf-8")

    if not compileall.compile_dir(str(root / "backend"), quiet=1):
        print(f"Patch written, but backend compilation failed. Backup: {backup}", file=sys.stderr)
        return 2
    if not compileall.compile_file(str(lambda_dir / "handler.py"), quiet=1):
        print(f"Patch written, but Lambda compilation failed. Backup: {backup}", file=sys.stderr)
        return 2

    print("OncoTwin Lambda + Gemini memory patch applied successfully.")
    print(f"Backup: {backup}")
    print("Created: backend/app/lambda_vectorizer.py")
    print("Updated: backend/app/config.py, backend/app/memory_routes.py")
    print("Created: aws/lambda_memory_vectorizer/*")
    print("Created: scripts/deploy_lambda_memory_vectorizer.sh")
    print("Created: AWS_LAMBDA_MEMORY.md")
    print("Next: bash scripts/deploy_lambda_memory_vectorizer.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
