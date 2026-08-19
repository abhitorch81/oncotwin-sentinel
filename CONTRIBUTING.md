# Contributing

Contributions that improve DataHub grounding, metadata-aware code generation, accessibility, reproducibility or research-safety boundaries are welcome.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DEMO_MODE=true pytest -q
bash scripts/12_local_demo.sh
```

Before opening a pull request:

```bash
python3 -m compileall -q backend/app
node --check frontend/assets/app.js
for script in scripts/*.sh; do bash -n "$script"; done
pytest -q
```

## Pull-request expectations

- Keep synthetic biology clearly separated from live DataHub/GCP operations.
- Never add credentials or patient-identifying data.
- Preserve the human approval boundary for mutations.
- Add or update tests for changed behavior.
- Document any new DataHub entity, aspect, tool or permission.

## Potential DataHub open-source contributions

High-value extensions include a reusable oncology metadata standard, a cancer-context DataHub Skill, improved MCP error handling and documentation for governed incident-to-writeback agent workflows.
