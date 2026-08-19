# OncoTwin MemoryMesh: CockroachDB agent memory
from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        future=True,
    )


def cockroach_health() -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            row = connection.execute(
                text("SELECT current_database() AS database_name, version() AS version, now() AS database_time")
            ).mappings().one()
            vector_index = connection.execute(
                text(
                    "SELECT count(*) FROM pg_indexes "
                    "WHERE tablename = 'agent_memories' "
                    "AND indexname = 'agent_memories_embedding_idx'"
                )
            ).scalar_one()
        return {
            "ok": True,
            "database": row["database_name"],
            "version": row["version"],
            "database_time": row["database_time"],
            "vector_index_ready": int(vector_index) == 1,
        }
    except (RuntimeError, SQLAlchemyError) as exc:
        return {"ok": False, "error": type(exc).__name__}
