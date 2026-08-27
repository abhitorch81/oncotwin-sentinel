import unittest

from apps.api.app.bounded_reruns import build_bounded_rerun_preview
from apps.api.app.child_reruns import PERSIST_CONFIRMATION, persist_bounded_rerun_child
from apps.api.app.memory import InMemoryMissionRepository
from apps.api.app.mission_service import MissionService
from apps.api.app.models import PersistRerunRequest


class PersistedChildRerunTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryMissionRepository()
        self.parent = MissionService(self.repository).start("Synthetic parent mission")
        self.preview = build_bounded_rerun_preview(
            self.parent,
            command="Reduce candidate B to 70 nm and rerun",
            selected_candidate_id="B",
            channel="text",
        )

    def request(self, **overrides):
        payload = {
            "actor": "demo-researcher",
            "channel": "ui",
            "confirmation": PERSIST_CONFIRMATION,
            "preview_id": self.preview.preview_id,
            "candidate_id": "B",
            "requested_size_nm": 70,
        }
        payload.update(overrides)
        return PersistRerunRequest(**payload)

    def test_explicit_ui_action_persists_unapproved_child_with_lineage(self):
        parent_hash = self.parent.receipt.receipt_sha256
        response = persist_bounded_rerun_child(self.repository, self.parent, self.request())
        child = response.child_mission

        self.assertTrue(response.persisted)
        self.assertEqual(response.parent_mission_id, self.parent.id)
        self.assertEqual(child.state, "awaiting_human_approval")
        self.assertFalse(child.approval_requested)
        self.assertIsNone(child.approved_by)
        self.assertEqual(child.lineage.parent_mission_id, self.parent.id)
        self.assertEqual(child.lineage.root_mission_id, self.parent.id)
        self.assertEqual(child.lineage.source_preview_id, self.preview.preview_id)
        self.assertEqual(child.lineage.candidate_id, "B")
        self.assertEqual(child.receipt.results[1].candidate.particle_size_nm, 70)
        self.assertNotEqual(child.receipt.receipt_sha256, parent_hash)
        self.assertEqual(self.repository.get(self.parent.id).receipt.receipt_sha256, parent_hash)

    def test_voice_cannot_persist_child(self):
        with self.assertRaisesRegex(PermissionError, "Voice and agents"):
            persist_bounded_rerun_child(
                self.repository,
                self.parent,
                self.request(channel="voice"),
            )
        self.assertEqual(self.repository.proof()["mission_count"], 1)

    def test_tampered_preview_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Preview identity"):
            persist_bounded_rerun_child(
                self.repository,
                self.parent,
                self.request(preview_id="preview-tampered"),
            )

    def test_retry_is_idempotent(self):
        first = persist_bounded_rerun_child(self.repository, self.parent, self.request())
        second = persist_bounded_rerun_child(self.repository, self.parent, self.request())
        self.assertEqual(first.child_mission.id, second.child_mission.id)
        self.assertEqual(first.child_mission.receipt.receipt_sha256, second.child_mission.receipt.receipt_sha256)
        self.assertEqual(self.repository.proof()["mission_count"], 2)


if __name__ == "__main__":
    unittest.main()
