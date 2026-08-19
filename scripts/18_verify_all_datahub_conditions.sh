#!/usr/bin/env bash
set -euo pipefail

: "${APP_URL:?Set APP_URL to the Cloud Run service URL}"

python3 - "${APP_URL%/}" <<'PY'
import json
import subprocess
import sys
import urllib.parse

base = sys.argv[1]
expected = {
    "feature_quality": "progression_features",
    "cancer_progression": "tumour_state_transitions",
    "model_drift": "cohort_drift_metrics",
    "schema_mutation": "genomic_schema_contract_events",
    "biomarker_discordance": "multi_omic_biomarker_evidence",
    "protein_conformation": "protein_conformation_states",
    "microenvironment_escape": "spatial_microenvironment_states",
}

receipts = []
for case_id, asset_name in expected.items():
    url = f"{base}/api/datahub/proof?{urllib.parse.urlencode({'case_id': case_id})}"
    # Use the platform curl CA store. Framework Python installations on macOS
    # can lack a populated OpenSSL trust bundle even when Safari/curl trust the
    # valid Cloud Run certificate.
    response = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--max-time", "180", url],
        check=True,
        capture_output=True,
        text=True,
    )
    proof = json.loads(response.stdout)
    assert proof["mode"] == "live", (case_id, proof["mode"])
    assert proof["source"] == "datahub-mcp", (case_id, proof["source"])
    assert proof["asset_name"] == asset_name, (case_id, proof["asset_name"])
    assert proof["all_tools_passed"], (case_id, proof["evidence"])
    assert proof["successful_tools"] == proof["total_tools"] == 6
    assert not proof["mutation_performed"]
    receipts.append({
        "case_id": case_id,
        "asset": asset_name,
        "urn": proof["asset_urn"],
        "receipt_sha256": proof["receipt_sha256"],
        "reads": "6/6",
    })

print(json.dumps({"status": "PASS", "datahub_native_conditions": "7/7", "receipts": receipts}, indent=2))
PY

echo "All seven conditions returned fresh, condition-specific DataHub MCP proof."
