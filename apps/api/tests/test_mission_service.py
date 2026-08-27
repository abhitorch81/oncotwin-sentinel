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

    def test_each_agent_step_emits_inspectable_artifact_and_scene_patch(self):
        mission = self.service.start("Investigate the resistant red clone")
        self.assertTrue(all(event.artifact for event in mission.events))
        self.assertTrue(all(event.scene_patch for event in mission.events))
        self.assertEqual(mission.events[0].artifact.metrics[0].value, 31)
        self.assertEqual(mission.events[2].scene_patch.simulation_hour, 24)
        self.assertEqual(mission.events[3].artifact.kind, "safety_decision")
        self.assertEqual(mission.events[-1].artifact.metrics[0].value, "BLOCKED")

    def test_receipt_contains_hourly_candidate_timeline(self):
        mission = self.service.start("Investigate the resistant red clone")
        self.assertEqual(len(mission.receipt.timeline), 75)
        self.assertEqual({frame.hour for frame in mission.receipt.timeline}, set(range(25)))
        at_zero = [frame for frame in mission.receipt.timeline if frame.hour == 0]
        self.assertTrue(all(frame.tumour_payload_release == 0 for frame in at_zero))
        final_c = next(frame for frame in mission.receipt.timeline if frame.hour == 24 and frame.candidate_id == "C")
        b_breach = next(frame.hour for frame in mission.receipt.timeline
                        if frame.candidate_id == "B" and frame.liver_accumulation > .45)
        result_c = next(result for result in mission.receipt.results if result.candidate.id == "C")
        self.assertEqual(b_breach, 18)
        self.assertEqual(final_c.tumour_payload_release, result_c.tumour_payload_release)
        self.assertEqual(final_c.liver_accumulation, result_c.liver_accumulation)


if __name__ == "__main__":
    unittest.main()
