#!/usr/bin/env bash
set -euo pipefail

ONCOTWIN_PORT="${ONCOTWIN_PORT:-8081}"
BASE_URL="${APP_URL:-http://localhost:${ONCOTWIN_PORT}}"
HEALTH_URL="${BASE_URL%/}/api/health"

payload="$(curl -fsS "${HEALTH_URL}")" || {
  echo "OncoTwin is not reachable at ${HEALTH_URL}"
  exit 1
}

python3 -c 'import json,sys; p=json.load(sys.stdin); assert p.get("ui_version")=="10.1.0", f"Wrong UI version: {p.get(chr(117)+chr(105)+chr(95)+chr(118)+chr(101)+chr(114)+chr(115)+chr(105)+chr(111)+chr(110))!r}"; print("Verified OncoTwin UI v10.1.0 · mode:", p["mode"])' <<<"${payload}"
