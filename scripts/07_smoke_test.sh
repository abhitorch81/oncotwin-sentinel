#!/usr/bin/env bash
set -euo pipefail

APP_URL="${APP_URL:-http://localhost:8080}"
curl --fail --silent "${APP_URL}/api/health" | python3 -m json.tool
curl --fail --silent -X POST "${APP_URL}/api/agents/run" \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which cancer progression datasets are trustworthy?"}' | python3 -m json.tool >/tmp/oncotwin-smoke.json
python3 - <<'PY'
import json
payload=json.load(open('/tmp/oncotwin-smoke.json'))
assert len(payload['traces']) == 6
assert payload['proposal']['requires_approval'] is True
print('Grounded six-agent workflow passed.')
PY

curl --fail --silent "${APP_URL}/api/missions/cases" > /tmp/oncotwin-cases.json
python3 - <<'PY'
import json
cases=json.load(open('/tmp/oncotwin-cases.json'))
assert [case['case_id'] for case in cases] == [
    'feature_quality', 'cancer_progression', 'model_drift', 'schema_mutation',
    'biomarker_discordance', 'protein_conformation', 'microenvironment_escape',
    'ctdna_mrd_rebound', 'bispecific_safety', 'cart_antigen_escape',
    'neoantigen_vaccine_drift', 'radiopharmaceutical_mismatch'
]
print('Twelve-case RL mission catalog passed.')
PY

curl --fail --silent "${APP_URL}/api/agentic/capabilities" > /tmp/oncotwin-agentic-capabilities.json
python3 - <<'PY'
import json
payload=json.load(open('/tmp/oncotwin-agentic-capabilities.json'))
assert payload['lanes']['local_fast']['transport'] == 'browser'
assert payload['lanes']['gemini_live']['transport'] == 'backend_websocket'
assert payload['lanes']['gemini_live']['fallback'] == 'browser_speech_and_local_router'
assert payload['safety']['voice_can_approve'] is False
assert payload['safety']['live_model_can_bypass_router'] is False
print('Agentic multimodal safety contract passed.')
PY
