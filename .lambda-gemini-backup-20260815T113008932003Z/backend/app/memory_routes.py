# OncoTwin MemoryMesh: CockroachDB agent memory
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .database import cockroach_health
from .memory_repository import patient_memory_bundle


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
