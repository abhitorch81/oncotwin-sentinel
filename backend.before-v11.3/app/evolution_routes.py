"""Mutation evolution API backed by CockroachDB."""
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .evolution_repository import evolution_graph, evolution_memory_replay, run_evolution_council, run_evolution_memory_paths

router = APIRouter(tags=["CockroachDB Mutation Evolution"])

class EvolutionCouncilRequest(BaseModel):
    horizon: int = Field(default=4, ge=1, le=8)

class EvolutionMemoryPathRequest(BaseModel):
    horizon: int = Field(default=4, ge=1, le=8)
    pressure_mode: str = Field(default="balanced", pattern="^(low|balanced|high)$")

@router.get("/api/evolution/patients/{synthetic_code}")
def get_evolution_graph(synthetic_code: str) -> dict[str, Any]:
    try: graph=evolution_graph(synthetic_code)
    except Exception as exc:
        raise HTTPException(503, detail={"message":"Evolution schema is unavailable. Run scripts/cockroach_evolution_v11_1.sql.","error_type":type(exc).__name__}) from exc
    if graph is None: raise HTTPException(404, detail="Synthetic patient not found")
    return graph

@router.post("/api/evolution/patients/{synthetic_code}/council")
def run_council(synthetic_code: str, request: EvolutionCouncilRequest) -> dict[str, Any]:
    try: result=run_evolution_council(synthetic_code,request.horizon)
    except Exception as exc:
        raise HTTPException(503, detail={"message":"Evolution council could not reach its CockroachDB evidence graph.","error_type":type(exc).__name__}) from exc
    if result is None: raise HTTPException(404, detail="Synthetic patient not found")
    return result

@router.get("/api/evolution/patients/{synthetic_code}/memory-replay")
def get_memory_replay(synthetic_code: str) -> dict[str, Any]:
    try: result=evolution_memory_replay(synthetic_code)
    except Exception as exc:
        raise HTTPException(503, detail={"message":"Evolution memory is unavailable. Run scripts/apply_evolution_memory_schema.py.","error_type":type(exc).__name__}) from exc
    if result is None: raise HTTPException(404, detail="Synthetic patient not found")
    return result

@router.post("/api/evolution/patients/{synthetic_code}/memory-paths")
def generate_memory_paths(synthetic_code: str, request: EvolutionMemoryPathRequest) -> dict[str, Any]:
    try: result=run_evolution_memory_paths(synthetic_code,request.horizon,request.pressure_mode)
    except Exception as exc:
        raise HTTPException(503, detail={"message":"Memory-conditioned paths could not be generated from CockroachDB evidence.","error_type":type(exc).__name__}) from exc
    if result is None: raise HTTPException(404, detail="Synthetic patient not found")
    return result
