import unittest

from apps.api.app.security import ApprovalDenied, validate_approval


class ApprovalPolicyTests(unittest.TestCase):
    def test_voice_cannot_approve(self):
        with self.assertRaises(ApprovalDenied):
            validate_approval("voice", "APPROVE SYNTHETIC RESEARCH MISSION")

    def test_confirmation_is_exact(self):
        with self.assertRaises(ApprovalDenied):
            validate_approval("ui", "approve")

    def test_explicit_ui_approval_passes(self):
        validate_approval("ui", "APPROVE SYNTHETIC RESEARCH MISSION")


if __name__ == "__main__":
    unittest.main()

