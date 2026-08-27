# Apply Production ADK Trace Persistence Repair

This hotfix persists privacy-safe Google ADK traces in Firestore so any Cloud Run instance
can serve `/adk-trace` and `/adk-events` after scaling, restart or redeployment.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Production_ADK_Trace_Repair.zip -d .

source .venv-adk/bin/activate
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Do not commit or deploy until a fresh local mission completes and its trace can be read
after restarting the API process.
