import asyncio
import unittest

from apps.api.app.adk_runtime import AdkExecutionService, AdkTraceRepository, translate_adk_event


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
        self.assertNotIn("args", str(payload))
        self.assertNotIn("must-not-persist", str(payload))

    def test_disabled_trace_is_explicit(self):
        async def scenario():
            repository = AdkTraceRepository()
            service = AdkExecutionService(repository)
            await service.prepare("nano-test", "gemini-2.5-flash", enabled=False)
            return await repository.get("nano-test")

        trace = asyncio.run(scenario())
        self.assertEqual(trace.status, "disabled")
        self.assertFalse(trace.model_call_executed)


if __name__ == "__main__":
    unittest.main()

