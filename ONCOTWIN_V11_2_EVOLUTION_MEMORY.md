# OncoTwin V11.2 — Persistent Evolution Memory

V11.2 turns CockroachDB memory into an active evolutionary reasoning system. The experience can replay immutable observation frames, generate several competing futures, preserve agent votes, and compare an earlier forecast with a later observation.

All biological records are synthetic research data. Paths are hypotheses, not individual predictions. No diagnosis or treatment recommendation is generated, and human review remains mandatory.

## What persistent memory now does

- Reconstructs four longitudinal clone-distribution frames after a restart.
- Animates those frames in the Three.js evolution graph.
- Calculates observed expansion and contraction deltas between timepoints.
- Conditions four competing paths on remembered evidence and agent memory.
- Persists every path, probability, vote, evidence reference and SHA-256 receipt.
- Reconciles an earlier forecast with a later observation and exposes surprises.

## New CockroachDB tables

- `evolution_memory_frames`: immutable longitudinal clone distributions.
- `evolution_path_hypotheses`: competing futures and five-agent vote records.
- `evolution_memory_reconciliations`: forecast-versus-observation divergence.

Together with the 11 existing V11.1 tables, OncoTwin now uses 14 CockroachDB tables plus the distributed vector index.

## Install over V11.1

Copy `backend`, `frontend` and `scripts` over the existing project. Preserve `.env.memorymesh.local` and all secrets.

```bash
cd ~/Downloads/oncotwin-datahub-v10
source .venv-crdb/bin/activate
set -a
source .env.memorymesh.local
set +a

python3 scripts/apply_evolution_memory_schema.py
uvicorn backend.app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>, choose **Evolution Lab**, replay the observations, change selection pressure and click **Evolve four remembered paths**.

## API verification

```bash
curl -sS http://127.0.0.1:8000/api/evolution/patients/ONCO-007/memory-replay | python3 -m json.tool

curl -sS -X POST \
  http://127.0.0.1:8000/api/evolution/patients/ONCO-007/memory-paths \
  -H 'Content-Type: application/json' \
  -d '{"horizon":4,"pressure_mode":"balanced"}' | python3 -m json.tool
```

Expected: four recalled frames, one prior reconciliation, four competing paths, five agent votes per new path, and CockroachDB-backed receipts.
