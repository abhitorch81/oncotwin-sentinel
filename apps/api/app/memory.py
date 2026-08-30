from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Protocol

from .models import Mission


def _serialized_receipt_context(receipt: dict[str, Any]) -> dict[str, Any]:
    digest = receipt.get("receipt_sha256") or ""
    if len(digest) < 12:
        return {}
    results = receipt.get("results") or []
    return {
        "receipt_sha256_prefix": digest[:12],
        "preferred_candidate_id": receipt.get("preferred_candidate_id"),
        "rejected_candidate_ids": receipt.get("rejected_candidate_ids") or [],
        "evidence_ids": (receipt.get("evidence_ids") or [])[:5],
        "candidate_outcomes": [
            {
                "candidate_id": (item.get("candidate") or {}).get("id"),
                "decision": item.get("decision"),
                "tumour_payload_release": item.get("tumour_payload_release"),
                "liver_accumulation": item.get("liver_accumulation"),
            }
            for item in results[:3]
        ],
    }


def _receipt_context(mission: Mission) -> dict[str, Any]:
    return _serialized_receipt_context(mission.receipt.model_dump(mode="json")) if mission.receipt else {}


class MissionRepository(Protocol):
    configured_backend: str

    def save(self, mission: Mission, resume_cursor: int | None = None) -> Mission: ...

    def get(self, mission_id: str) -> Mission | None: ...

    def relevant_receipts(self, limit: int = 3) -> list[str]: ...

    def recent_receipt_context(self, limit: int = 3) -> list[dict[str, Any]]: ...

    def record_image_evidence(self, evidence: dict[str, Any]) -> None: ...

    def get_image_evidence(self, evidence_id: str) -> dict[str, Any] | None: ...

    def record_approval(
        self, mission: Mission, actor: str, decision: str, channel: str
    ) -> Mission: ...

    def proof(self) -> dict[str, Any]: ...

    def close(self) -> None: ...


class InMemoryMissionRepository:
    """Truthful process-local fallback implementing the repository boundary."""

    configured_backend = "in_memory"

    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}
        self._resume_cursors: dict[str, int] = {}
        self._approval_events: dict[tuple[str, str], dict[str, str]] = {}
        self._image_evidence: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def save(self, mission: Mission, resume_cursor: int | None = None) -> Mission:
        with self._lock:
            self._missions[mission.id] = deepcopy(mission)
            self._resume_cursors[mission.id] = (
                len(mission.events) if resume_cursor is None else resume_cursor
            )
            return deepcopy(mission)

    def get(self, mission_id: str) -> Mission | None:
        with self._lock:
            mission = self._missions.get(mission_id)
            return deepcopy(mission) if mission else None

    def relevant_receipts(self, limit: int = 3) -> list[str]:
        with self._lock:
            missions = sorted(self._missions.values(), key=lambda item: item.created_at)
            receipts = [
                mission.receipt.receipt_sha256[:12]
                for mission in missions
                if mission.receipt
            ]
            return receipts[-limit:]

    def recent_receipt_context(self, limit: int = 3) -> list[dict[str, Any]]:
        with self._lock:
            missions = sorted(self._missions.values(), key=lambda item: item.created_at)
            return [_receipt_context(item) for item in missions if item.receipt][-limit:]

    def record_image_evidence(self, evidence: dict[str, Any]) -> None:
        with self._lock:
            self._image_evidence[evidence["evidence_id"]] = deepcopy(evidence)

    def get_image_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        with self._lock:
            evidence = self._image_evidence.get(evidence_id)
            return deepcopy(evidence) if evidence else None

    def record_approval(
        self, mission: Mission, actor: str, decision: str, channel: str
    ) -> Mission:
        with self._lock:
            saved = self.save(mission)
            self._approval_events[(mission.id, decision)] = {
                "mission_id": mission.id,
                "actor": actor,
                "decision": decision,
                "channel": channel,
            }
            return saved

    def proof(self) -> dict[str, Any]:
        with self._lock:
            receipts = self.relevant_receipts(limit=1)
            return {
                "configured_backend": self.configured_backend,
                "active_backend": self.configured_backend,
                "persistent": False,
                "healthy": True,
                "degraded": False,
                "mission_count": len(self._missions),
                "approval_count": len(self._approval_events),
                "image_evidence_count": len(self._image_evidence),
                "latest_receipt_sha256_prefix": receipts[-1] if receipts else None,
                "resume_cursor_supported": True,
            }

    def close(self) -> None:
        return None


class FirestoreMissionRepository:
    """Google-native durable mission memory using Firestore Native mode."""

    configured_backend = "firestore"

    def __init__(
        self,
        project_id: str,
        *,
        database: str = "(default)",
        missions_collection: str = "missions",
        receipts_collection: str = "mission_receipts",
        approvals_collection: str = "approval_events",
        image_evidence_collection: str = "image_evidence",
        client: Any | None = None,
        firestore_module: Any | None = None,
    ) -> None:
        if client is None or firestore_module is None:
            from google.cloud import firestore

            firestore_module = firestore
            client = firestore.Client(
                project=project_id or None,
                database=database,
            )
        self._client = client
        self._firestore = firestore_module
        self._missions = client.collection(missions_collection)
        self._receipts = client.collection(receipts_collection)
        self._approvals = client.collection(approvals_collection)
        self._image_evidence = client.collection(image_evidence_collection)

    def _mission_payload(self, mission: Mission, resume_cursor: int) -> dict[str, Any]:
        return {
            "mission": mission.model_dump(mode="json"),
            "mission_id": mission.id,
            "state": mission.state,
            "prompt": mission.prompt,
            "created_at": mission.created_at,
            "updated_at": self._firestore.SERVER_TIMESTAMP,
            "resume_cursor": resume_cursor,
            "receipt_sha256": (
                mission.receipt.receipt_sha256 if mission.receipt else None
            ),
            "synthetic_research_only": True,
        }

    def _receipt_payload(self, mission: Mission) -> dict[str, Any] | None:
        if mission.receipt is None:
            return None
        return {
            "mission_id": mission.id,
            "created_at": mission.created_at,
            "receipt_sha256": mission.receipt.receipt_sha256,
            "receipt": mission.receipt.model_dump(mode="json"),
            "synthetic_research_only": True,
        }

    def save(self, mission: Mission, resume_cursor: int | None = None) -> Mission:
        cursor = len(mission.events) if resume_cursor is None else resume_cursor
        batch = self._client.batch()
        batch.set(
            self._missions.document(mission.id),
            self._mission_payload(mission, cursor),
            merge=True,
        )
        receipt = self._receipt_payload(mission)
        if receipt:
            batch.set(self._receipts.document(mission.id), receipt, merge=True)
        batch.commit()
        return deepcopy(mission)

    def get(self, mission_id: str) -> Mission | None:
        snapshot = self._missions.document(mission_id).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict() or {}
        serialized_mission = payload.get("mission")
        return Mission.model_validate(serialized_mission) if serialized_mission else None

    def relevant_receipts(self, limit: int = 3) -> list[str]:
        safe_limit = max(1, min(limit, 20))
        query = (
            self._receipts
            .order_by(
                "created_at",
                direction=self._firestore.Query.DESCENDING,
            )
            .limit(safe_limit)
        )
        newest_first = [
            (snapshot.to_dict() or {}).get("receipt_sha256", "")[:12]
            for snapshot in query.stream()
        ]
        return [receipt for receipt in reversed(newest_first) if receipt]

    def recent_receipt_context(self, limit: int = 3) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 10))
        query = self._receipts.order_by(
            "created_at", direction=self._firestore.Query.DESCENDING
        ).limit(safe_limit)
        contexts = []
        for snapshot in query.stream():
            payload = snapshot.to_dict() or {}
            receipt = payload.get("receipt") or {}
            contexts.append(_serialized_receipt_context(receipt))
        return list(reversed([item for item in contexts if item]))

    def record_image_evidence(self, evidence: dict[str, Any]) -> None:
        safe = deepcopy(evidence)
        safe.pop("raw_bytes", None)
        safe["created_at"] = self._firestore.SERVER_TIMESTAMP
        safe["synthetic_research_only"] = True
        safe["raw_image_persisted"] = False
        self._image_evidence.document(safe["evidence_id"]).set(safe, merge=True)

    def get_image_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        snapshot = self._image_evidence.document(evidence_id).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict() or {}
        payload.pop("created_at", None)
        return payload

    def record_approval(
        self, mission: Mission, actor: str, decision: str, channel: str
    ) -> Mission:
        mission_ref = self._missions.document(mission.id)
        event_ref = self._approvals.document(f"{mission.id}:{decision}")
        transaction = self._client.transaction(max_attempts=5)

        @self._firestore.transactional
        def commit_approval(active_transaction: Any) -> None:
            existing = event_ref.get(transaction=active_transaction)
            active_transaction.set(
                mission_ref,
                self._mission_payload(mission, len(mission.events)),
                merge=True,
            )
            if not existing.exists:
                active_transaction.create(
                    event_ref,
                    {
                        "mission_id": mission.id,
                        "actor": actor,
                        "decision": decision,
                        "channel": channel,
                        "created_at": self._firestore.SERVER_TIMESTAMP,
                        "synthetic_research_only": True,
                    },
                )

        commit_approval(transaction)
        return deepcopy(mission)

    @staticmethod
    def _bounded_count(collection: Any, limit: int = 1000) -> int:
        return sum(1 for _ in collection.limit(limit).stream())

    def proof(self) -> dict[str, Any]:
        latest_query = (
            self._receipts
            .order_by(
                "created_at",
                direction=self._firestore.Query.DESCENDING,
            )
            .limit(1)
        )
        latest = next(iter(latest_query.stream()), None)
        latest_payload = latest.to_dict() if latest else {}
        latest_hash = (latest_payload or {}).get("receipt_sha256")
        return {
            "configured_backend": self.configured_backend,
            "active_backend": self.configured_backend,
            "persistent": True,
            "healthy": True,
            "degraded": False,
            "mission_count": self._bounded_count(self._missions),
            "approval_count": self._bounded_count(self._approvals),
            "image_evidence_count": self._bounded_count(self._image_evidence),
            "latest_receipt_sha256_prefix": latest_hash[:12] if latest_hash else None,
            "resume_cursor_supported": True,
        }

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if close:
            close()


class ResilientMissionRepository:
    """Uses Firestore first and explicitly degrades only in demo mode."""

    configured_backend = "firestore"

    def __init__(
        self,
        primary: MissionRepository,
        fallback: InMemoryMissionRepository,
        *,
        allow_fallback: bool,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._allow_fallback = allow_fallback
        self._last_error_type: str | None = None

    def _degrade(self, error: Exception) -> None:
        self._last_error_type = type(error).__name__
        if not self._allow_fallback:
            raise error

    def save(self, mission: Mission, resume_cursor: int | None = None) -> Mission:
        try:
            result = self._primary.save(mission, resume_cursor)
            self._last_error_type = None
            self._fallback.save(result, resume_cursor)
            return result
        except Exception as error:
            self._degrade(error)
            return self._fallback.save(mission, resume_cursor)

    def get(self, mission_id: str) -> Mission | None:
        try:
            mission = self._primary.get(mission_id)
            self._last_error_type = None
            if mission:
                self._fallback.save(mission)
                return mission
        except Exception as error:
            self._degrade(error)
        return self._fallback.get(mission_id)

    def relevant_receipts(self, limit: int = 3) -> list[str]:
        try:
            receipts = self._primary.relevant_receipts(limit)
            self._last_error_type = None
            return receipts
        except Exception as error:
            self._degrade(error)
            return self._fallback.relevant_receipts(limit)

    def recent_receipt_context(self, limit: int = 3) -> list[dict[str, Any]]:
        try:
            contexts = self._primary.recent_receipt_context(limit)
            self._last_error_type = None
            return contexts
        except Exception as error:
            self._degrade(error)
            return self._fallback.recent_receipt_context(limit)

    def record_image_evidence(self, evidence: dict[str, Any]) -> None:
        try:
            self._primary.record_image_evidence(evidence)
            self._last_error_type = None
            self._fallback.record_image_evidence(evidence)
        except Exception as error:
            self._degrade(error)
            self._fallback.record_image_evidence(evidence)

    def get_image_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        try:
            evidence = self._primary.get_image_evidence(evidence_id)
            self._last_error_type = None
            if evidence:
                self._fallback.record_image_evidence(evidence)
                return evidence
        except Exception as error:
            self._degrade(error)
        return self._fallback.get_image_evidence(evidence_id)

    def record_approval(
        self, mission: Mission, actor: str, decision: str, channel: str
    ) -> Mission:
        try:
            result = self._primary.record_approval(mission, actor, decision, channel)
            self._last_error_type = None
            self._fallback.record_approval(result, actor, decision, channel)
            return result
        except Exception as error:
            self._degrade(error)
            return self._fallback.record_approval(mission, actor, decision, channel)

    def proof(self) -> dict[str, Any]:
        try:
            proof = self._primary.proof()
            self._last_error_type = None
            return {**proof, "fallback_enabled": self._allow_fallback}
        except Exception as error:
            self._degrade(error)
            fallback = self._fallback.proof()
            return {
                **fallback,
                "configured_backend": self.configured_backend,
                "active_backend": "in_memory",
                "persistent": False,
                "degraded": True,
                "fallback_enabled": self._allow_fallback,
                "last_error_type": self._last_error_type,
            }

    def close(self) -> None:
        self._primary.close()
        self._fallback.close()


class _UnavailableMissionRepository:
    """Defers a sanitized initialization failure into the demo fallback boundary."""

    configured_backend = "firestore"

    def __init__(self, error: Exception) -> None:
        self._error = error

    def _raise(self, *args: Any, **kwargs: Any) -> Any:
        raise self._error

    save = get = relevant_receipts = recent_receipt_context = record_image_evidence = get_image_evidence = record_approval = proof = _raise

    def close(self) -> None:
        return None


def create_mission_repository(
    *,
    firestore_enabled: bool,
    project_id: str,
    firestore_database: str,
    demo_mode: bool,
    client: Any | None = None,
    firestore_module: Any | None = None,
) -> MissionRepository:
    if not firestore_enabled:
        return InMemoryMissionRepository()
    try:
        primary: MissionRepository = FirestoreMissionRepository(
            project_id,
            database=firestore_database,
            client=client,
            firestore_module=firestore_module,
        )
    except Exception as error:
        if not demo_mode:
            raise
        primary = _UnavailableMissionRepository(error)
    return ResilientMissionRepository(
        primary,
        InMemoryMissionRepository(),
        allow_fallback=demo_mode,
    )
