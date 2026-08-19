#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

ONCOTWIN_PORT="${ONCOTWIN_PORT:-8080}"

echo "Starting OncoTwin 3D v6.0 on http://localhost:${ONCOTWIN_PORT}"
echo "Expected header: OncoTwin 3D · DataHub DEMO · V10.1.0"

DEMO_MODE=true .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port "${ONCOTWIN_PORT}"
