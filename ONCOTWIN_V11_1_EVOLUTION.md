# OncoTwin V11.1 — CockroachDB Mutation Evolution Intelligence

V11.1 adds a persistent clonal-evolution graph and an interactive 3D Evolution Lab. All biology is synthetic, all projections are research simulations, and every conclusion stops at a human-review gate.

## New CockroachDB data products

- `evolution_clones`: clone generation, prevalence, fitness, risk and mutation payloads.
- `evolution_edges`: evidence-backed parent/child transitions.
- `mutation_events`: time-stamped mutations with evidence strength and deduplication hashes.
- `evolution_snapshots`: immutable graph receipts, counterfactual projections and council decisions.
- `evolution_agent_insights`: persisted conclusions and handoffs from five agents.

## Tandem-agent chain

1. Genomic Cartographer maps alterations and clone lineage.
2. Clonal Evolution Forecaster simulates competitive fitness.
3. Evidence Challenger identifies weak or inferred branches.
4. Memory Sentinel rehydrates prior CockroachDB agent memory.
5. Safety Governor enforces the research-only boundary and hands control to a human reviewer.

## Install

Copy the `backend`, `frontend` and `scripts` folders over the existing project, preserving your existing `.env.memorymesh.local` and secrets.

```bash
cd ~/Downloads/oncotwin-datahub-v10
source .venv-crdb/bin/activate

set -a
source .env.memorymesh.local
set +a

python3 scripts/apply_evolution_schema.py
uvicorn backend.app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000> and select **Evolution Lab**.

## Verify

```bash
curl -sS http://127.0.0.1:8000/api/evolution/patients/ONCO-007 | python3 -m json.tool

curl -sS -X POST \
  http://127.0.0.1:8000/api/evolution/patients/ONCO-007/council \
  -H 'Content-Type: application/json' \
  -d '{"horizon":4}' | python3 -m json.tool
```

Expected: five clones, four evolutionary edges, four mutation events, a five-agent council, four-generation trajectories, and graph/decision SHA-256 receipts.
