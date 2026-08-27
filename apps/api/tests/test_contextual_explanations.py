import unittest

from apps.api.app.contextual_explanations import build_contextual_explanation
from apps.api.app.memory import InMemoryMissionRepository
from apps.api.app.mission_service import MissionService


class ContextualExplanationTests(unittest.TestCase):
    def setUp(self):
        repository = InMemoryMissionRepository()
        service = MissionService(repository)
        service.start("Prior synthetic mission")
        self.mission = service.start("Current synthetic mission")

    def test_rejected_candidate_focuses_first_policy_breach(self):
        response = build_contextual_explanation(
            self.mission,
            question="Why was candidate B rejected?",
            selected_candidate_id="B",
            simulation_hour=24,
            channel="text",
        )
        self.assertEqual(response.candidate_id, "B")
        self.assertEqual(response.decision, "rejected")
        self.assertEqual(response.focus_hour, 18)
        self.assertEqual(response.scene_patch.camera_target, "liver_sink")
        self.assertIn("45%", response.explanation)
        self.assertIn("68%", response.explanation)
        self.assertIn("Approval still requires a human", response.spoken_text)
        self.assertFalse(response.approval_granted)

    def test_selected_preferred_candidate_uses_current_hour(self):
        response = build_contextual_explanation(
            self.mission,
            question="Explain the selected candidate",
            selected_candidate_id="C",
            simulation_hour=12,
            channel="scene",
        )
        self.assertEqual(response.candidate_id, "C")
        self.assertEqual(response.focus_hour, 12)
        self.assertEqual(response.scene_patch.camera_target, "tumour_core")
        self.assertEqual(response.scene_patch.simulation_hour, 12)

    def test_question_can_identify_candidate_without_scene_selection(self):
        response = build_contextual_explanation(
            self.mission,
            question="Why was candidate B rejected?",
            selected_candidate_id=None,
            simulation_hour=24,
            channel="voice",
        )
        self.assertEqual(response.candidate_id, "B")
        self.assertEqual(response.channel, "voice")

    def test_legacy_receipt_without_timeline_is_reconstructed(self):
        self.mission.receipt.timeline = []
        response = build_contextual_explanation(
            self.mission,
            question="Why was candidate B rejected?",
            selected_candidate_id="B",
            simulation_hour=24,
            channel="text",
        )
        self.assertEqual(response.focus_hour, 18)
        self.assertIn("LEGACY-RECEIPT-TIMELINE-RECONSTRUCTED-V1", response.evidence_ids)
        self.assertIn("68%", response.explanation)


if __name__ == "__main__":
    unittest.main()
