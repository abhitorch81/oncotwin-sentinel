# Apply Living Mission Theatre — Checkpoint 2D

This overlay adds adaptive render quality, reduced-motion behavior, and a WebGL safe mode.
It assumes checkpoint 2C is committed on `feature/living-mission-theatre`.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_2D.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Start the local API and web app as before, run a fresh Nano Safety Mission, and verify:

1. Camera choreography, candidate selection, particle paths, quarantine, and the approval
   membrane still work normally.
2. The footer reports `3D HIGH`, `3D BALANCED`, or `3D CONSERVATIVE` followed by
   `ADAPTIVE`; the renderer can lower its pixel density and sparkle count under pressure.
3. In Chrome DevTools, open **Rendering**, enable **Emulate CSS media feature
   prefers-reduced-motion: reduce**, and reload. The footer must report
   `3D CONSERVATIVE · REDUCED MOTION`.
4. In reduced-motion mode, camera shots snap to their targets and pulsing, floating,
   particle-flow, tumour-spin, and boundary-spin animations stop. Candidate selection and
   manual orbit controls remain usable.
5. The browser console has no React, Three.js, or WebGL errors during a full mission.

The WebGL fallback is deliberately non-destructive: if graphics initialization or the
graphics context fails, the agent rail, evidence receipt, candidate results, and human
approval boundary remain available outside the canvas.
