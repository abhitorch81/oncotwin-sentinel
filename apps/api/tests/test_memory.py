import unittest
from unittest.mock import patch

from apps.api.app.memory import (
    InMemoryMissionRepository,
    ResilientMissionRepository,
    create_mission_repository,
)
from apps.api.app.mission_service import MissionService


class _UnavailablePrimary:
    configured_backend = "firestore"

    def _fail(self, *args, **kwargs):
        raise ConnectionError("secret connection detail must not escape")

    save = get = relevant_receipts = record_approval = proof = _fail

    def close(self):
        return None


class MemoryRepositoryTests(unittest.TestCase):
    def test_in_memory_proof_is_truthful(self):
        proof = InMemoryMissionRepository().proof()
        self.assertFalse(proof["persistent"])
        self.assertEqual(proof["active_backend"], "in_memory")

    def test_approval_is_auditable_and_idempotent(self):
        repository = InMemoryMissionRepository()
        mission = MissionService(repository).start("Synthetic mission")
        mission.state = "approved"
        mission.approved_by = "judge"
        repository.record_approval(mission, "judge", "approved", "ui")
        repository.record_approval(mission, "judge", "approved", "ui")
        proof = repository.proof()
        self.assertEqual(proof["approval_count"], 1)
        self.assertEqual(repository.get(mission.id).state, "approved")

    def test_resume_cursor_contract_is_reported(self):
        repository = InMemoryMissionRepository()
        MissionService(repository).start("Synthetic mission")
        self.assertTrue(repository.proof()["resume_cursor_supported"])

    def test_demo_degrades_without_leaking_error_text(self):
        repository = ResilientMissionRepository(
            _UnavailablePrimary(), InMemoryMissionRepository(), allow_fallback=True
        )
        mission = MissionService(repository).start("Synthetic mission")
        proof = repository.proof()
        self.assertIsNotNone(repository.get(mission.id))
        self.assertTrue(proof["degraded"])
        self.assertEqual(proof["last_error_type"], "ConnectionError")
        self.assertNotIn("secret connection detail", str(proof))

    def test_live_mode_fails_closed(self):
        repository = ResilientMissionRepository(
            _UnavailablePrimary(), InMemoryMissionRepository(), allow_fallback=False
        )
        with self.assertRaises(ConnectionError):
            MissionService(repository).start("Synthetic mission")

    def test_firestore_initialization_failure_degrades_in_demo(self):
        with patch(
            "apps.api.app.memory.FirestoreMissionRepository",
            side_effect=RuntimeError("credential payload must not escape"),
        ):
            repository = create_mission_repository(
                firestore_enabled=True,
                project_id="demo-project",
                firestore_database="(default)",
                demo_mode=True,
            )
        proof = repository.proof()
        self.assertTrue(proof["degraded"])
        self.assertEqual(proof["last_error_type"], "RuntimeError")
        self.assertNotIn("credential payload", str(proof))


if __name__ == "__main__":
    unittest.main()
