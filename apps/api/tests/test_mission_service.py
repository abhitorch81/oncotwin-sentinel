import unittest

from apps.api.app.memory import InMemoryMissionRepository
from apps.api.app.mission_service import MissionService


class MissionServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryMissionRepository()
        self.service = MissionService(self.repository)

    def test_mission_stops_for_human_approval(self):
        mission = self.service.start("Investigate the resistant red clone")
        self.assertEqual(mission.state, "awaiting_human_approval")
        self.assertEqual(mission.events[-1].status, "blocked")

    def test_only_four_visible_agent_names(self):
        mission = self.service.start("Investigate the resistant red clone")
        self.assertEqual(
            {event.agent for event in mission.events},
            {"Evidence Scout", "Nano Designer", "Twin Simulator", "Safety Steward"},
        )

    def test_receipt_contains_decision_and_hash(self):
        mission = self.service.start("Investigate the resistant red clone")
        self.assertEqual(mission.receipt.preferred_candidate_id, "C")
        self.assertEqual(mission.receipt.rejected_candidate_ids, ["B"])
        self.assertEqual(len(mission.receipt.receipt_sha256), 64)

    def test_next_mission_retrieves_prior_receipt(self):
        first = self.service.start("First investigation")
        second = self.service.start("Follow-up investigation")
        self.assertIn(first.receipt.receipt_sha256[:12], second.receipt.prior_memory_used)


if __name__ == "__main__":
    unittest.main()

