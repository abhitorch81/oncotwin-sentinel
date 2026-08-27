# Apply Checkpoint 3E — Gemini 3.5 eligibility

This checkpoint upgrades the governed Google ADK workflow to stable `gemini-3.5-flash`
through Vertex AI and adds a non-billable eligibility proof endpoint.

## Local verification

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
source .venv-adk/bin/activate

export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_CLOUD_PROJECT="project-1f5f7d56-1029-4c78-a68"
export GOOGLE_CLOUD_LOCATION="global"
export GEMINI_MODEL="gemini-3.5-flash"
export ADK_MODEL="gemini-3.5-flash"
export FIRESTORE_ENABLED="true"
export FIRESTORE_DATABASE="(default)"
export ADK_ENABLED="true"

git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

After starting the API, verify:

```bash
curl -sS http://127.0.0.1:8000/api/health | python3 -m json.tool
curl -sS http://127.0.0.1:8000/api/agentic/adk/proof | python3 -m json.tool
curl -sS http://127.0.0.1:8000/api/eligibility/proof | python3 -m json.tool
```

Do not mark the requirement complete until a new production mission trace reports model
`gemini-3.5-flash`, status `succeeded`, `model_call_executed: true`, and no fallback reason.
