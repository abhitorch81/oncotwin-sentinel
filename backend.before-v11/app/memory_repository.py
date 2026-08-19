# OncoTwin MemoryMesh: CockroachDB agent memory
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
