# Google ADK Fortified Fleet

OncoTwin Sentinel uses Google Agent Development Kit (ADK) as a real
multi-agent orchestration layer, not only as a dependency label. Every governed
mission is passed through a programmatic ADK `SequentialAgent` containing four
Gemini 3.5+ `LlmAgent` specialists.

| Agent | Responsibility | Authority |
|---|---|---|
| EvidenceScout | Calls the sanitized read-only mission tool and grounds claims | Read only |
| TwinAnalyst | Maps evidence to synthetic 3D twin state and uncertainty | Research interpretation only |
| RepairPlanner | Proposes a reversible workflow repair | Proposal only |
| SafetySteward | Enforces medical-use and human-approval boundaries | Veto/escalation only |

## Execution contract

1. `MissionManager` gathers DataHub and digital-twin evidence and calculates
   the deterministic safety policy.
2. `sanitized_mission_context` removes raw evidence payloads, tokens and
   approval material.
3. ADK `Runner` executes `OncoTwinFortifiedFleet` with an isolated session.
4. Agent-authored events are reduced to a small judge-facing trace.
5. MissionManager records the trace and remains stopped at
   `awaiting_approval`.
6. ADK has no mutation tool, approval secret or clinical-action permission.

In local demo mode, the same four-agent contract is rendered as a deterministic
trace without calling Gemini. In live mode, ADK uses the configured Gemini 3.5+
model. Dependency, credential, timeout or provider failures return a
`safe_fallback` result and never weaken the existing approval boundary.

## Judge proof

```bash
curl -s "$APP_URL/api/adk/capabilities" | python3 -m json.tool
curl -s "$APP_URL/api/adk/registry" | python3 -m json.tool
curl -s "$APP_URL/api/health" | python3 -m json.tool
```

Run **Start an ADK investigation** in the Multimodal Command Center. The UI
shows the four ADK specialists, model, orchestration mode and final safety
summary. The mission remains visibly locked until a human uses the existing
approval control.

## Local setup

```bash
python -m pip install -r requirements.txt
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT"
export GOOGLE_CLOUD_LOCATION=global
export GEMINI_MODEL=gemini-3.5-flash
```

The exact model ID must be available in the selected Google project and region.
