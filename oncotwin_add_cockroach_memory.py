#!/usr/bin/env python3
"""Patch OncoTwin DataHub v10.1 with a CockroachDB agent-memory API.

Run from the repository root:
    python3 oncotwin_add_cockroach_memory.py

The patch is idempotent, never reads or prints DATABASE_URL, and creates a
timestamped backup of every existing file it changes.
"""

from __future__ import annotations

import argparse
import compileall
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


MARKER = "# OncoTwin MemoryMesh: CockroachDB agent memory"

DATABASE_PY = '''# OncoTwin MemoryMesh: CockroachDB agent memory
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
'''

MEMORY_REPOSITORY_PY = '''# OncoTwin MemoryMesh: CockroachDB agent memory
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text

from .config import get_settings
from .database import get_engine


def _rows(connection: Any, statement: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(text(statement), parameters).mappings().all()]


def patient_memory_bundle(synthetic_code: str) -> dict[str, Any] | None:
    settings = get_settings()
    parameters = {
        "tenant_id": settings.memory_tenant_id,
        "synthetic_code": synthetic_code.upper(),
    }
    with get_engine().connect() as connection:
        patient_row = connection.execute(
            text(
                "SELECT tenant_id, patient_id, synthetic_code, cancer_type, cancer_stage, metadata, created_at "
                "FROM patients WHERE tenant_id = CAST(:tenant_id AS UUID) "
                "AND synthetic_code = :synthetic_code"
            ),
            parameters,
        ).mappings().first()
        if patient_row is None:
            return None

        patient = dict(patient_row)
        scoped = {
            "tenant_id": str(patient["tenant_id"]),
            "patient_id": str(patient["patient_id"]),
        }
        events = _rows(
            connection,
            "SELECT event_id, event_type, event_time, payload, source_name, source_uri, evidence_hash "
            "FROM clinical_events WHERE tenant_id = CAST(:tenant_id AS UUID) "
            "AND patient_id = CAST(:patient_id AS UUID) ORDER BY event_time DESC",
            scoped,
        )
        runs = _rows(
            connection,
            "SELECT run_id, mission, agent_name, status, current_step, checkpoint, input_context, "
            "output_context, idempotency_key, started_at, completed_at FROM agent_runs "
            "WHERE tenant_id = CAST(:tenant_id AS UUID) AND patient_id = CAST(:patient_id AS UUID) "
            "ORDER BY started_at DESC",
            scoped,
        )
        memories = _rows(
            connection,
            "SELECT memory_id, run_id, memory_type, title, content, metadata, confidence, "
            "source_agent, created_at, embedding IS NOT NULL AS embedded FROM agent_memories "
            "WHERE tenant_id = CAST(:tenant_id AS UUID) AND patient_id = CAST(:patient_id AS UUID) "
            "ORDER BY created_at DESC",
            scoped,
        )
        handoffs = _rows(
            connection,
            "SELECT handoff_id, run_id, from_agent, to_agent, reason, context, context_hash, created_at "
            "FROM agent_handoffs WHERE tenant_id = CAST(:tenant_id AS UUID) "
            "AND patient_id = CAST(:patient_id AS UUID) ORDER BY created_at DESC",
            scoped,
        )
        approvals = _rows(
            connection,
            "SELECT approval_id, run_id, action_type, proposed_action, decision, reviewer, "
            "reviewer_comment, evidence_hash, requested_at, decided_at FROM approvals "
            "WHERE tenant_id = CAST(:tenant_id AS UUID) AND patient_id = CAST(:patient_id AS UUID) "
            "ORDER BY requested_at DESC",
            scoped,
        )

    receipt_source = {
        "synthetic_code": patient["synthetic_code"],
        "event_ids": [str(item["event_id"]) for item in events],
        "run_ids": [str(item["run_id"]) for item in runs],
        "memory_ids": [str(item["memory_id"]) for item in memories],
        "handoff_ids": [str(item["handoff_id"]) for item in handoffs],
        "approval_ids": [str(item["approval_id"]) for item in approvals],
    }
    receipt_hash = hashlib.sha256(
        json.dumps(receipt_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "source": "cockroachdb-persistent-memory",
        "restart_rehydratable": True,
        "patient": patient,
        "clinical_events": events,
        "agent_runs": runs,
        "agent_memories": memories,
        "agent_handoffs": handoffs,
        "approvals": approvals,
        "memory_receipt": {
            "sha256": receipt_hash,
            "counts": {
                "events": len(events),
                "runs": len(runs),
                "memories": len(memories),
                "handoffs": len(handoffs),
                "approvals": len(approvals),
            },
        },
    }
'''

MEMORY_ROUTES_PY = '''# OncoTwin MemoryMesh: CockroachDB agent memory
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
'''


def require_anchor(content: str, anchor: str, file_name: str) -> None:
    if anchor not in content:
        raise RuntimeError(f"Required anchor not found in {file_name}: {anchor!r}")


def patch_once(content: str, anchor: str, replacement: str, file_name: str) -> str:
    if replacement in content:
        return content
    require_anchor(content, anchor, file_name)
    return content.replace(anchor, replacement, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="OncoTwin repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    main_py = root / "backend/app/main.py"
    config_py = root / "backend/app/config.py"
    requirements = root / "requirements.txt"
    for path in (main_py, config_py, requirements):
        if not path.is_file():
            raise SystemExit(f"Not an OncoTwin v10 root; missing {path.relative_to(root)}")

    main_content = main_py.read_text(encoding="utf-8")
    config_content = config_py.read_text(encoding="utf-8")
    req_content = requirements.read_text(encoding="utf-8")

    main_content = patch_once(
        main_content,
        "from .mission_control import MissionManager\n",
        "from .mission_control import MissionManager\nfrom .memory_routes import router as memory_router\n",
        "backend/app/main.py",
    )
    main_content = patch_once(
        main_content,
        "mission_manager = MissionManager(settings)\n",
        "mission_manager = MissionManager(settings)\napp.include_router(memory_router)\n",
        "backend/app/main.py",
    )
    config_content = patch_once(
        config_content,
        '    mission_store_path: str = "/tmp/oncotwin-missions"\n',
        '    mission_store_path: str = "/tmp/oncotwin-missions"\n\n'
        '    # OncoTwin MemoryMesh: CockroachDB agent memory\n'
        '    database_url: str = ""\n'
        '    memory_tenant_id: str = "11111111-1111-1111-1111-111111111111"\n',
        "backend/app/config.py",
    )

    additions = [
        "sqlalchemy>=2.0,<3",
        "sqlalchemy-cockroachdb>=2.0,<3",
        "psycopg2-binary>=2.9,<3",
    ]
    existing_names = {
        re.split(r"[<>=!~]", line, maxsplit=1)[0].strip().lower()
        for line in req_content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing = [
        line
        for line in additions
        if re.split(r"[<>=!~]", line, maxsplit=1)[0].lower() not in existing_names
    ]
    if missing:
        req_content = req_content.rstrip() + "\n" + "\n".join(missing) + "\n"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / f".cockroach-backup-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    for path in (main_py, config_py, requirements):
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    main_py.write_text(main_content, encoding="utf-8")
    config_py.write_text(config_content, encoding="utf-8")
    requirements.write_text(req_content, encoding="utf-8")
    (root / "backend/app/database.py").write_text(DATABASE_PY, encoding="utf-8")
    (root / "backend/app/memory_repository.py").write_text(MEMORY_REPOSITORY_PY, encoding="utf-8")
    (root / "backend/app/memory_routes.py").write_text(MEMORY_ROUTES_PY, encoding="utf-8")

    if not compileall.compile_dir(str(root / "backend"), quiet=1):
        print(f"Patch written, but Python compilation failed. Backup: {backup}", file=sys.stderr)
        return 2

    print("OncoTwin CockroachDB memory patch applied successfully.")
    print(f"Backup: {backup}")
    print("Created: backend/app/database.py")
    print("Created: backend/app/memory_repository.py")
    print("Created: backend/app/memory_routes.py")
    print("Updated: backend/app/config.py, backend/app/main.py, requirements.txt")
    if os.environ.get("DATABASE_URL"):
        print("DATABASE_URL detected (value not displayed).")
    else:
        print("DATABASE_URL is not set in this shell.")
    print("Next: python -m pip install -r requirements.txt")
    print("Then: uvicorn backend.app.main:app --host 127.0.0.1 --port 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
