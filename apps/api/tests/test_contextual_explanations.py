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

    def test_followup_is_grounded_in_same_mission_image_evidence(self):
        response = build_contextual_explanation(
            self.mission,
            question="How does this image affect candidate B?",
            selected_candidate_id="B",
            simulation_hour=18,
            channel="voice",
            image_evidence={
                "mission_id": self.mission.id,
                "evidence_id": "IMG-1234567890AB",
                "selected_candidate_id": "B",
                "synthetic_pattern": "clustered",
                "r7_similarity": .82,
                "matrix_resistance_signal": .71,
                "confidence": .88,
            },
        )
        self.assertEqual(response.image_evidence_id, "IMG-1234567890AB")
        self.assertIn("82% R7 similarity", response.explanation)
        self.assertIn("does not alter", response.explanation)
        self.assertIn("IMG-1234567890AB", response.evidence_ids)


if __name__ == "__main__":
    unittest.main()
