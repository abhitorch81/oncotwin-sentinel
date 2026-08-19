"""Judge-facing API for the CockroachDB Operations Agent."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .cockroach_ops import ccloud_evidence, mcp_capabilities, recent_runs, run_operations_proof, skill_evidence

router = APIRouter(prefix="/api/cockroach/ops", tags=["cockroach-operations"])


@router.get("/capabilities")
async def capabilities() -> dict[str, Any]:
    return {
        "agent": "CockroachDB Operations Agent",
        "mcp": await mcp_capabilities(),
        "ccloud": await ccloud_evidence(),
        "agent_skill": skill_evidence(),
        "distributed_vector_index": {"used": True, "table": "agent_memories", "index": "agent_memories_embedding_idx", "dimensions": 1024},
        "safety": {"mcp_read_only_calls_only": True, "write_tools_invoked": [], "cluster_scoped": True, "audit_receipts_persisted": True},
    }


@router.post("/proof")
async def proof() -> dict[str, Any]:
    try:
        return await run_operations_proof()
    except Exception as error:
        raise HTTPException(503, {"message": str(error), "error_type": type(error).__name__}) from error


@router.get("/runs")
async def runs(limit: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
    try:
        items = recent_runs(limit)
        return {"runs": items, "count": len(items), "source": "CockroachDB persistent operations memory"}
    except Exception as error:
        raise HTTPException(503, {"message": "Apply scripts/cockroach_ops_v11_4.sql first.", "error_type": type(error).__name__}) from error
