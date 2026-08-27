import asyncio
from copy import deepcopy
import unittest

from apps.api.app.adk_runtime import (
    AdkExecutionService,
    AdkTraceRepository,
    FirestoreAdkTraceRepository,
    create_adk_trace_repository,
    translate_adk_event,
)
from apps.api.app.models import AdkMissionTrace, AdkTraceEvent


class _Snapshot:
    def __init__(self, payload):
        self.payload = payload
        self.exists = payload is not None

    def to_dict(self):
        return deepcopy(self.payload)


class _Document:
    def __init__(self, client, collection, document_id):
        self.client = client
        self.key = (collection, document_id)

    def get(self):
        return _Snapshot(deepcopy(self.client.store.get(self.key)))


class _Collection:
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def document(self, document_id):
        return _Document(self.client, self.name, document_id)


class _Batch:
    def __init__(self, client):
        self.client = client
        self.operations = []

    def set(self, document, payload, merge=False):
        self.operations.append((document, deepcopy(payload), merge))

    def commit(self):
        for document, payload, merge in self.operations:
            if merge:
                existing = deepcopy(self.client.store.get(document.key, {}))
                existing.update(payload)
                payload = existing
            self.client.store[document.key] = deepcopy(payload)


class _Client:
    def __init__(self):
        self.store = {}
        self.closed = False

    def collection(self, name):
        return _Collection(self, name)

    def batch(self):
        return _Batch(self)

    def close(self):
        self.closed = True


class _Firestore:
    SERVER_TIMESTAMP = "server-timestamp"


class _Call:
    name = "simulate_nano_candidate"
    args = {"candidate_id": "B", "secret": "must-not-persist"}


class _Event:
    author = "twin_simulator"
    node_name = "twin_simulator"
    model_reasoning = "must-not-persist"

    def get_function_calls(self):
        return [_Call()]

    def is_final_response(self):
        return False


class AdkRuntimeTests(unittest.TestCase):
    def test_translation_keeps_metadata_not_arguments(self):
        translated = translate_adk_event(_Event(), 1)
        payload = translated.model_dump()
        self.assertEqual(payload["visible_agent"], "Twin Simulator")
        self.assertEqual(payload["tool_names"], ["simulate_nano_candidate"])
        self.assertEqual(payload["phase"], "tool_call")
        self.assertEqual(payload["scene_action"], "run_particle_paths")
        self.assertEqual(payload["artifact"]["kind"], "distribution_comparison")
        self.assertEqual(payload["scene_patch"]["camera_target"], "tumour_core")
        self.assertIn("24 h", payload["summary"])
        self.assertNotIn("args", str(payload))
        self.assertNotIn("must-not-persist", str(payload))

    def test_evidence_translation_uses_mission_memory_count(self):
        class EvidenceEvent(_Event):
            author = "evidence_scout"
            node_name = "evidence_scout"

            def get_function_calls(self):
                return [type("Call", (), {"name": "retrieve_synthetic_clone_evidence"})()]

        translated = translate_adk_event(EvidenceEvent(), 1, memory_count=3)
        payload = translated.model_dump()
        self.assertIn("recovered 3 prior mission receipts", payload["summary"])
        prior_receipts = next(
            metric for metric in payload["artifact"]["metrics"]
            if metric["label"] == "Prior receipts"
        )
        self.assertEqual(prior_receipts["value"], 3)

    def test_disabled_trace_is_explicit(self):
        async def scenario():
            repository = AdkTraceRepository()
            service = AdkExecutionService(repository)
            await service.prepare("nano-test", "gemini-3.5-flash", enabled=False)
            return await repository.get("nano-test")

        trace = asyncio.run(scenario())
        self.assertEqual(trace.status, "disabled")
        self.assertFalse(trace.model_call_executed)

    def test_final_event_is_complete_without_tool_arguments(self):
        class FinalEvent(_Event):
            def get_function_calls(self):
                return []

            def is_final_response(self):
                return True

        translated = translate_adk_event(FinalEvent(), 2)
        self.assertEqual(translated.phase, "complete")
        self.assertEqual(translated.tool_names, [])

    def test_firestore_trace_survives_repository_reconstruction(self):
        async def scenario():
            client = _Client()
            first = FirestoreAdkTraceRepository(
                "test-project", client=client, firestore_module=_Firestore
            )
            trace = AdkMissionTrace(
                mission_id="nano-durable",
                status="succeeded",
                model="gemini-3.5-flash",
                model_call_executed=True,
                events=[
                    AdkTraceEvent(
                        sequence=1,
                        author="evidence_scout",
                        visible_agent="Evidence Scout",
                        node_name="evidence_scout",
                        event_type="Event",
                        final_response=True,
                        phase="complete",
                    )
                ],
            )
            await first.save(trace)
            reconstructed = FirestoreAdkTraceRepository(
                "test-project", client=client, firestore_module=_Firestore
            )
            restored = await reconstructed.get("nano-durable")
            return trace, restored, client.store

        trace, restored, store = asyncio.run(scenario())
        self.assertEqual(restored, trace)
        payload = store[("adk_traces", "nano-durable")]
        self.assertNotIn("prompt", payload)
        self.assertNotIn("credentials", str(payload))
        self.assertNotIn("reasoning", str(payload))

    def test_trace_factory_uses_memory_when_firestore_is_disabled(self):
        repository = create_adk_trace_repository(
            firestore_enabled=False,
            project_id="",
            firestore_database="(default)",
            demo_mode=True,
        )
        self.assertEqual(repository.configured_backend, "in_memory")


if __name__ == "__main__":
    unittest.main()
