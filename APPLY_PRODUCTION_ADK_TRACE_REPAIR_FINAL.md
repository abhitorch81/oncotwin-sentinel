# Apply Production ADK Trace Persistence Repair — Final

This final overlay records participant verification and reapplies the complete durable
ADK trace repair.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Production_ADK_Trace_Repair_Final.zip -d .

source .venv-adk/bin/activate
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

Verified with mission `nano-11f4dfd2dc`: the succeeded Gemini/ADK trace, 12 translated
events and null fallback reason remained retrievable after restarting the API process.
