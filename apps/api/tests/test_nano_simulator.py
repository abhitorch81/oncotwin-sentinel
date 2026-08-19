import unittest

from apps.api.app.nano_simulator import DEFAULT_CANDIDATES, receipt_digest, run_comparison, simulate


class NanoSimulatorTests(unittest.TestCase):
    def test_is_deterministic(self):
        self.assertEqual(simulate(DEFAULT_CANDIDATES[0]), simulate(DEFAULT_CANDIDATES[0]))

    def test_candidate_b_is_rejected(self):
        results = {result.candidate.id: result for result in run_comparison()}
        self.assertEqual(results["B"].decision, "rejected")
        self.assertGreater(results["B"].liver_accumulation, .45)

    def test_one_preferred_candidate(self):
        results = run_comparison()
        self.assertEqual(sum(result.decision == "preferred" for result in results), 1)

    def test_receipt_hash_is_stable(self):
        self.assertEqual(receipt_digest({"b": 2, "a": 1}), receipt_digest({"a": 1, "b": 2}))


if __name__ == "__main__":
    unittest.main()

