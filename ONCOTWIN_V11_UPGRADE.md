# OncoTwin V11 — Cancer Decision Multiverse

This release replaces the decorative organ viewer with a Decision Forge and expands the governed mission catalog from seven to twelve current cancer-research topics.

## What changed

- Decision Forge with real CockroachDB semantic-memory recall through the existing AWS Lambda/FastEmbed path.
- Twelve research missions, including MET resistance, ctDNA MRD rebound, spatial immune escape, ADC payload resistance, bispecific safety, CAR-T antigen escape, neoantigen drift, digital pathology shift, multi-omic discordance and radiopharmaceutical mismatch.
- Three-agent council votes and five counterfactual actions per mission.
- Deterministic Q-learning selection, decision margin and SHA-256 decision receipt.
- Twelve-world interactive Proof Galaxy.
- Human approval remains mandatory; clinical action is explicitly prohibited.

## Install on the Mac

From the project root:

```bash
cd ~/Downloads/oncotwin-datahub-v10
cp -R backend backend.before-v11
cp -R frontend frontend.before-v11
```

Copy the extracted V11 `backend` and `frontend` folders over the project folders, then restart:

```bash
source .venv-crdb/bin/activate
set -a
source .env.memorymesh.local
set +a
uvicorn backend.app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>, select **Decision Forge**, choose a mission and click **Run this decision**.

## Verification

```bash
curl -sS http://127.0.0.1:8000/api/health | python3 -m json.tool
curl -sS http://127.0.0.1:8000/api/missions/cases | python3 -m json.tool
curl -sS -X POST http://127.0.0.1:8000/api/memory/patients/ONCO-007/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"emerging MET mediated resistance","limit":1}' | python3 -m json.tool
```

Expected: UI version `11.0.0`, twelve missions, and a CockroachDB memory match. No database URL, API key or approval secret is included in this package.
