# OncoTwin V11.3 — Genome Helix Memory Lab

V11.3 removes the former scRNA tab and replaces it with a judge-facing Genome Helix Memory Lab. The visualization is a data-bound Three.js double helix—not decorative DNA. Mutation events place rupture hotspots, CockroachDB observation frames change the helix through time, and saved evolution paths create a translucent forecast helix for observed-versus-forecast pairing.

## Signature experience

1. Play the persistent observation chain from founder sequence to resistance.
2. Switch among observed, paired and mutation-rupture modes.
3. Choose one of four memory-conditioned evolutionary paths.
4. Generate the next deterministic synthetic observation.
5. Persist that frame and its forecast reconciliation in CockroachDB.
6. Inspect clone expansion/contraction and the new SHA-256 frame receipt.

## Persistent-memory utility

- Previous frames define the prior clone distribution.
- A saved path supplies the forecast distribution.
- Evidence strength controls how much the forecast influences the new observation.
- The system deliberately introduces a small deterministic evidence surprise.
- CockroachDB stores the resulting frame and forecast divergence.
- Every subsequent agent council can recall the enlarged observation history.

## No new migration required

V11.3 uses the V11.2 tables already installed:

- `evolution_memory_frames`
- `evolution_path_hypotheses`
- `evolution_memory_reconciliations`

## Install over V11.2

```bash
cd ~/Downloads/oncotwin-datahub-v10

cp -R ../oncotwin-v11.3-genome-helix/backend/. backend/
cp -R ../oncotwin-v11.3-genome-helix/frontend/. frontend/
cp -R ../oncotwin-v11.3-genome-helix/scripts/. scripts/

source .venv-crdb/bin/activate
set -a
source .env.memorymesh.local
set +a

export DATABASE_URL="$(
  aws secretsmanager get-secret-value \
    --region ap-south-1 \
    --secret-id oncotwin/memory-vectorizer \
    --query SecretString \
    --output text |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["database_url"])'
)"

uvicorn backend.app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>, select **Genome Helix**, play progression, select a path and generate the next observation.

## API verification

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/evolution/patients/ONCO-007/observations/generate \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"resistance_sweep","evidence_strength":0.82}' |
python3 -m json.tool
```

All biology remains synthetic and research-only. No clinical action is generated.
