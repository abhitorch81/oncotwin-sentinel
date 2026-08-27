# Apply Living Mission Theatre — Checkpoint 3B Final

This consolidated overlay includes Checkpoint 3B, restored-mission compatibility, and the
final panel-layout repair. When Safety Steward answers a contextual question, its receipt
evidence becomes the single active panel instead of overlapping the candidate inspector.
Closing the explanation restores the selected candidate inspector.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3B_Final.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart the frontend after applying. Restore or run a mission, select candidate B, and
click `ASK SAFETY STEWARD WHY`.

Verify:

1. The candidate inspector is replaced by one unobstructed Safety Steward explanation.
2. The 45% ceiling, T+18H breach, T+24H value, evidence IDs, and receipt prefix are visible.
3. Closing the explanation restores the candidate inspector for B.
4. Selecting C and asking again displays its current-hour explanation.
5. The browser console is clean and no new mission is created.

Do not commit until participant visual verification passes.
