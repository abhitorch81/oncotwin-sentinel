#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "Node.js is required."; exit 1; }
npx --yes skills add cockroachlabs/cockroachdb-skills

echo "Official CockroachDB Agent Skills installed."
echo "Verify reviewing-cluster-health/SKILL.md is selected by the installer."
