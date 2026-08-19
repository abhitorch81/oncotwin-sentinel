#!/usr/bin/env bash
set -euo pipefail

command -v brew >/dev/null || { echo "Homebrew is required: https://brew.sh"; exit 1; }
command -v ccloud >/dev/null || brew install cockroachdb/tap/ccloud
echo "Installed ccloud: $(command -v ccloud)"
echo "Next, run: ccloud auth login"
echo "OncoTwin uses the managed CockroachDB Cloud MCP server at https://cockroachlabs.cloud/mcp."
