# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
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
    client = genai.Client(api_key=api_key)
    try:
        result = client.models.embed_content(
            model=MODEL_ID,
            contents=text_value,
            config=config,
        )
        values = list(result.embeddings[0].values)
    finally:
        client.close()
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
