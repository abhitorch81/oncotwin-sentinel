import json
import unittest

from apps.api.app.image_evidence import analyze_synthetic_image, safe_filename, validate_image
from apps.api.app.memory import InMemoryMissionRepository
from apps.api.app.mission_service import MissionService


class _Response:
    text = json.dumps({
        "synthetic_pattern": "clustered",
        "r7_similarity": 0.82,
        "matrix_resistance_signal": 0.71,
        "confidence": 0.88,
        "summary": "Synthetic clustered signal is consistent with the bounded R7 pattern.",
        "spoken_text": "Evidence Scout found a clustered synthetic pattern with eighty two percent R7 similarity.",
        "observations": ["Clustered high-intensity regions", "Heterogeneous boundary signal"],
        "prior_receipt_comparisons": [{
            "receipt_sha256_prefix": "1234567890ab",
            "relationship": "consistent",
            "summary": "Pattern is directionally consistent with the prior synthetic receipt.",
        }],
    })


class _Models:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return _Response()


class _Client:
    def __init__(self):
        self.models = _Models()


class _Types:
    class Part:
        @staticmethod
        def from_bytes(**kwargs):
            return kwargs

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs


class ImageEvidenceTests(unittest.TestCase):
    def test_rejects_spoofed_or_oversized_images(self):
        with self.assertRaises(ValueError):
            validate_image(b"not an image", "image/png")
        with self.assertRaises(ValueError):
            validate_image(b"\x89PNG\r\n\x1a\n" + b"x" * (5 * 1024 * 1024), "image/png")

    def test_sanitizes_filename(self):
        self.assertEqual(safe_filename("../../patient slide.png", "image/png"), "patient-slide.png")

    def test_returns_gemini_grounded_provenance_without_raw_bytes(self):
        repository = InMemoryMissionRepository()
        mission = MissionService(repository).start("Synthetic image mission")
        result = analyze_synthetic_image(
            data=b"\x89PNG\r\n\x1a\nsynthetic",
            filename="slide.png",
            mime_type="image/png",
            mission=mission,
            selected_candidate_id="B",
            simulation_hour=18,
            prior_receipts=[{"receipt_sha256_prefix": "1234567890ab"}],
            project_id="test-project",
            location="global",
            model="gemini-3.5-flash",
            client=_Client(),
            types_module=_Types,
        )
        self.assertEqual(result.model, "gemini-3.5-flash")
        self.assertTrue(result.model_call_executed)
        self.assertFalse(result.raw_image_persisted)
        self.assertEqual(result.selected_candidate_id, "B")
        self.assertEqual(result.scene_patch.simulation_hour, 18)
        self.assertEqual(result.prior_receipt_comparisons[0].receipt_sha256_prefix, "1234567890ab")


if __name__ == "__main__":
    unittest.main()
