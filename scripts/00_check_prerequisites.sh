#!/usr/bin/env bash
set -euo pipefail

for command_name in gcloud bq curl openssl; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
done

if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
  echo "Set GCP_PROJECT_ID before continuing." >&2
  exit 1
fi

echo "Prerequisites look good for project ${GCP_PROJECT_ID}."

