#!/usr/bin/env bash
set -euo pipefail

: "${APP_URL:?Set APP_URL to the Cloud Run URL}"
: "${WRITEBACK_APPROVAL_SECRET:?Set WRITEBACK_APPROVAL_SECRET locally}"

MISSION_JSON="$(curl --fail --silent -X POST "${APP_URL}/api/missions/start" \
  -H 'Content-Type: application/json' \
  --data '{"case_id":"feature_quality","cohort":"LUAD","mode":"live"}')"

MISSION_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["mission_id"])' <<<"${MISSION_JSON}")"
echo "Captured live feature-quality mission: ${MISSION_ID}"

BEFORE_PROOF="$(curl --fail --silent "${APP_URL}/api/datahub/proof?case_id=feature_quality")"
python3 -c '
import json,sys
p=json.load(sys.stdin)
assert p["mode"] == "live", p
assert p["all_tools_passed"] is True, p["evidence"]
assert p["active_incidents"] is not None and p["active_incidents"] >= 1, p
print("Before approval: active DataHub incident verified; MCP reads passed.")
' <<<"${BEFORE_PROOF}"

APPROVAL_PAYLOAD="$(python3 -c 'import json,os; print(json.dumps({"approval_secret": os.environ["WRITEBACK_APPROVAL_SECRET"]}))')"
RESULT="$(curl --fail --silent -X POST "${APP_URL}/api/missions/${MISSION_ID}/approve" \
  -H 'Content-Type: application/json' \
  --data "${APPROVAL_PAYLOAD}")"

python3 -c '
import json,sys
payload=json.load(sys.stdin)
proof=next(event for event in payload["events"] if event["type"] == "governance_verified")
event_types={event["type"] for event in payload["events"]}
assert payload["status"] == "completed"
assert proof["evidence"]["execution_scope"] == "live-datahub"
assert proof["evidence"]["active_incidents_after"] == 0
assert proof["evidence"]["repair_executed"] is True
assert proof["evidence"]["quality_validation_passed"] is True
assert proof["evidence"]["incident_resolved"] is True
assert proof["evidence"]["knowledge_written_back"] is True
assert proof["evidence"]["knowledge_inherited_verified"] is True
assert {"repair_executed", "quality_validated", "incident_resolved", "knowledge_written"} <= event_types
print(json.dumps({"mission_id": payload["mission_id"], "status": payload["status"], "governance_proof": proof["evidence"]}, indent=2))
' <<<"${RESULT}"

AFTER_PROOF="$(curl --fail --silent "${APP_URL}/api/datahub/proof?case_id=feature_quality")"
python3 -c '
import json,sys
p=json.load(sys.stdin)
assert p["all_tools_passed"] is True, p["evidence"]
assert p["active_incidents"] == 0, p
print("After approval: zero active incidents and fresh MCP verification passed.")
' <<<"${AFTER_PROOF}"

echo "Full governed writeback workflow passed. Save this output for the judge evidence pack."
