import unittest

from apps.api.app.adk_fleet import (
    VISIBLE_AGENTS,
    apply_nano_safety_policy,
    design_bounded_nano_candidates,
    retrieve_synthetic_clone_evidence,
    simulate_nano_candidate,
)


class AdkFleetContractTests(unittest.TestCase):
    def test_exactly_four_visible_agents(self):
        self.assertEqual([agent["visible_name"] for agent in VISIBLE_AGENTS], [
            "Evidence Scout", "Nano Designer", "Twin Simulator", "Safety Steward"
        ])

    def test_evidence_is_synthetic_and_grounded(self):
        result = retrieve_synthetic_clone_evidence("R7")
        self.assertTrue(result["synthetic_research_only"])
        self.assertEqual(result["status"], "grounded")

    def test_designer_returns_only_bounded_candidates(self):
        self.assertEqual([item["id"] for item in design_bounded_nano_candidates()["candidates"]], ["A", "B", "C"])

    def test_simulator_rejects_unknown_candidate(self):
        self.assertEqual(simulate_nano_candidate("Z")["status"], "rejected_input")

    def test_steward_cannot_approve(self):
        result = apply_nano_safety_policy()
        self.assertEqual(result["rejected_candidate_ids"], ["B"])
        self.assertEqual(result["preferred_candidate_id"], "C")
        self.assertFalse(result["approval_granted"])
        self.assertTrue(result["human_approval_required"])


if __name__ == "__main__":
    unittest.main()

