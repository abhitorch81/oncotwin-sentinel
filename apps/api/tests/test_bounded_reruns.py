import unittest

from apps.api.app.bounded_reruns import build_bounded_rerun_preview, is_bounded_rerun_command
from apps.api.app.memory import InMemoryMissionRepository
from apps.api.app.mission_service import MissionService


class BoundedRerunTests(unittest.TestCase):
    def setUp(self):
        self.mission = MissionService(InMemoryMissionRepository()).start("Synthetic parent mission")

    def test_candidate_b_can_be_previewed_at_70_nm_without_mutating_parent(self):
        original_hash = self.mission.receipt.receipt_sha256
        original_size = self.mission.receipt.results[1].candidate.particle_size_nm
        response = build_bounded_rerun_preview(
            self.mission,
            command="Reduce candidate B to 70 nm and rerun",
            selected_candidate_id="B",
            channel="text",
        )
        self.assertEqual(response.kind, "bounded_rerun")
        self.assertEqual(response.change.previous_value, 92)
        self.assertEqual(response.change.requested_value, 70)
        self.assertEqual(response.after.candidate.particle_size_nm, 70)
        self.assertEqual(len(response.timeline), 75)
        self.assertFalse(response.persisted)
        self.assertFalse(response.approval_granted)
        self.assertEqual(self.mission.receipt.receipt_sha256, original_hash)
        self.assertEqual(self.mission.receipt.results[1].candidate.particle_size_nm, original_size)

    def test_size_outside_research_envelope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "35–120 nm"):
            build_bounded_rerun_preview(
                self.mission,
                command="Reduce candidate B to 12 nm and rerun",
                selected_candidate_id="B",
                channel="voice",
            )

    def test_candidate_can_be_taken_from_command(self):
        response = build_bounded_rerun_preview(
            self.mission,
            command="Reduce candidate B to 70 nanometres and rerun",
            selected_candidate_id=None,
            channel="text",
        )
        self.assertEqual(response.candidate_id, "B")

    def test_only_explicit_size_reruns_use_preview_path(self):
        self.assertTrue(is_bounded_rerun_command("Reduce B to 70 nm and rerun"))
        self.assertFalse(is_bounded_rerun_command("Why was candidate B rejected?"))


if __name__ == "__main__":
    unittest.main()
