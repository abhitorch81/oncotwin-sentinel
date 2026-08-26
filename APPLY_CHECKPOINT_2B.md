# Apply Living Mission Theatre — Checkpoint 2B

This overlay adds the agent-driven 3D scene-state layer. It assumes checkpoint 2A is
already committed on `feature/living-mission-theatre`.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_2B.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Run a fresh Nano Safety Mission and verify each state:

1. Evidence Scout surrounds R7 with an animated signal lock and evidence pins.
2. Nano Designer opens three labelled holographic forge slots.
3. Twin Simulator animates A/B/C particles through distribution curves; B flows toward
   the liver while C concentrates on the tumour.
4. Safety Steward creates a red quarantine cage at the liver sink and labels the policy
   breach.
5. The final state surrounds the twin with a three-dimensional human-authority membrane.

The overlays should change in a deliberate 6–7 second sequence, preserve manual orbit
after camera moves, and remain legible without hiding the evidence receipt or approval
controls.
