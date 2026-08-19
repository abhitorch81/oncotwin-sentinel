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
    'biomarker_discordance', 'protein_conformation', 'microenvironment_escape'
]
print('Seven-case RL mission catalog passed.')
PY
