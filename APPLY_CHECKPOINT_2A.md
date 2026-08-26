# Apply Living Mission Theatre — Checkpoint 2A

This overlay adds agent-directed camera choreography. It assumes checkpoint 1 is already
committed on `feature/living-mission-theatre`.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_2A.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Start the API and frontend, clear `oncotwin.activeMissionId`, and launch a fresh Nano
Safety Mission. Confirm that the camera visits these five shots in order:

1. `clone r7` — Evidence Scout isolates the resistant clone.
2. `candidate forge` — Nano Designer opens the design view.
3. `tumour core` — Twin Simulator moves into the delivery comparison.
4. `liver sink` — Safety Steward focuses the off-target risk.
5. `approval boundary` — the theatre widens at the human authority boundary.

The camera should ease between shots. After each move settles, mouse orbit should work
again. With macOS Reduce Motion enabled, the camera should snap safely instead.
