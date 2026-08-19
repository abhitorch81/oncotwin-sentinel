# Milestone 2 — Google ADK fleet

## Slice 1: topology and bounded tools

This slice defines four real Google ADK `Agent` instances as explicit nodes in an ADK 2 graph workflow. Each agent receives only its bounded Python function tool. Fleet construction and the proof endpoint do not call Gemini, so they can be verified without spending model quota.

The existing deterministic mission service remains the active judge-demo path until Slice 2 translates live ADK Runner events into the established SSE and 3D scene-action contract.

## Local proof

Use Python 3.13 for the ADK environment.

```bash
pip install -r apps/api/requirements.txt
python3 scripts/verify_adk_fleet.py
curl -s http://127.0.0.1:8000/api/agentic/adk/proof | python3 -m json.tool
```

Expected: `installed: true`, four visible agents, coordinator `oncotwin_nano_safety_fleet`, workflow `ADK2GraphWorkflow`, and `model_call_executed: false`.

## Safety boundary

The Safety Steward tool always returns `approval_granted: false`. The separate visual approval endpoint remains the only approval path, and voice remains prohibited from granting approval.
