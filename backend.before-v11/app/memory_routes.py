# OncoTwin MemoryMesh: CockroachDB agent memory
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from .database import cockroach_health
from .memory_repository import patient_memory_bundle
from .lambda_vectorizer import VectorizerError, invoke_memory_vectorizer


router = APIRouter(tags=["CockroachDB Agent Memory"])


@router.get("/api/cockroach/health")
def cockroachdb_health() -> dict[str, Any]:
    result = cockroach_health()
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result)
    return result


@router.get("/api/memory/patients/{synthetic_code}")
def get_patient_memory(synthetic_code: str) -> dict[str, Any]:
    bundle = patient_memory_bundle(synthetic_code)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Synthetic patient memory not found")
    return bundle


@router.get("/api/memory/patients/{synthetic_code}/receipt")
def get_patient_memory_receipt(synthetic_code: str) -> dict[str, Any]:
    bundle = patient_memory_bundle(synthetic_code)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Synthetic patient memory not found")
    return {
        "synthetic_code": synthetic_code.upper(),
        "source": bundle["source"],
        "restart_rehydratable": bundle["restart_rehydratable"],
        "memory_receipt": bundle["memory_receipt"],
    }
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
