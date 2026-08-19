# All Things Agentic submission draft

## Category

**Fortified Enterprise Fleet**

## Project

**OncoTwin Sentinel: Living Evidence**

OncoTwin Sentinel is a Google ADK multi-agent oncology research digital twin
that turns governed evidence into visible 3D decisions. Four Gemini 3.5+
specialists coordinate evidence grounding, twin interpretation, reversible
repair planning and safety review while persistent memory, audit traces and a
human approval gate prevent autonomous clinical or external mutation.

## Required technology proof

- Gemini 3.5+ is configured as the primary model through Vertex AI.
- Google ADK `Runner`, `SequentialAgent`, four `LlmAgent` specialists and a
  read-only function tool are implemented in `backend/app/adk_fleet.py`.
- FastAPI and the full browser experience are deployed on Google Cloud Run.
- BigQuery supplies governed research data and validation jobs.
- `/api/health`, `/api/adk/capabilities` and `/api/adk/registry` expose
  machine-readable, secret-free proof.

## Operational workflow

1. DataHub-grounded telemetry raises a synthetic research mission.
2. A deterministic Q-learning policy blocks unsafe model consumption.
3. Google ADK coordinates four versioned specialist agents.
4. The 3D interface renders the evidence and ADK trace.
5. RepairPlanner proposes a reversible workflow action.
6. SafetySteward stops at visible human approval.
7. Only the existing guarded MissionManager can execute an approved external
   write; replay can never repeat it.

## Built with

Gemini 3.5 Flash, Google Agent Development Kit, Google GenAI SDK, Vertex AI,
Cloud Run, BigQuery, Secret Manager, FastAPI, Three.js, DataHub MCP,
CockroachDB MemoryMesh, AWS Lambda, LangChain and tabular Q-learning.

## Required submission assets

- Hosted Cloud Run URL
- Public GitHub repository
- Approximately four-minute demo video showing Cloud Run/Vertex proof
- Architecture diagram showing browser, Cloud Run, ADK fleet, Gemini, memory,
  BigQuery, DataHub and the human approval boundary
- Reproducible setup and testing instructions
- Start date in MM-DD-YY format

## Bonus plan

- Public LinkedIn progress/demo post using `#AllThingsAgenticHackathon`
- Public technical build article explicitly stating it was created for this
  hackathon
- Optional additional Google model integration only if it strengthens the
  product rather than becoming a decorative API call
