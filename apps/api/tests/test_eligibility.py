import unittest

from apps.api.app.eligibility import (
    build_eligibility_proof,
    gemini_version,
    meets_minimum_gemini_version,
)


class EligibilityProofTests(unittest.TestCase):
    def test_version_gate_rejects_older_or_unversioned_models(self):
        self.assertFalse(meets_minimum_gemini_version("gemini-2.5-flash"))
        self.assertFalse(meets_minimum_gemini_version("gemini-3-flash"))
        self.assertFalse(meets_minimum_gemini_version("gemini-flash-latest"))
        self.assertTrue(meets_minimum_gemini_version("gemini-3.5-flash"))
        self.assertTrue(meets_minimum_gemini_version("gemini-4.0-pro"))
        self.assertEqual(gemini_version("gemini-3.5-flash"), (3, 5))

    def test_all_three_requirements_must_be_configured(self):
        proof = build_eligibility_proof(
            model="gemini-3.5-flash",
            vertex_ai_enabled=True,
            adk_status={
                "installed": True,
                "enabled": True,
                "version": "2.7.1",
                "workflow": "ADK2GraphWorkflow",
            },
            firestore_configured=True,
            cloud_run_target=True,
        )
        self.assertTrue(proof["requirements_met"])
        self.assertEqual(proof["gemini"]["access"], "vertex_ai")
        self.assertEqual(proof["agent_framework"]["name"], "Google ADK")
        self.assertEqual(proof["google_cloud_infrastructure"]["services"], ["Cloud Run", "Firestore"])

    def test_proof_fails_closed_when_vertex_ai_is_not_configured(self):
        proof = build_eligibility_proof(
            model="gemini-3.5-flash",
            vertex_ai_enabled=False,
            adk_status={"installed": True, "enabled": True},
            firestore_configured=True,
            cloud_run_target=False,
        )
        self.assertFalse(proof["requirements_met"])
        self.assertFalse(proof["gemini"]["configured"])


if __name__ == "__main__":
    unittest.main()
