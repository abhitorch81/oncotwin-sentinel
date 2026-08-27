# Apply Living Mission Theatre — Checkpoint 3B v2

This consolidated overlay includes Checkpoint 3B plus the restored-mission compatibility
repair. Firestore missions created before Checkpoint 3A have an empty receipt timeline;
the command service now reconstructs the identical deterministic 0–24H kinetics in
memory so contextual questions work without mutating the historical receipt or hash.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3B_v2.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart only the backend after applying. Reload the existing mission
`nano-7932c56075`, select candidate B, and ask `Why was candidate B rejected?`.

Verify that `/commands` returns 200, the timeline moves to T+18H, the camera focuses the
liver sink, and the explanation includes the evidence ID
`LEGACY-RECEIPT-TIMELINE-RECONSTRUCTED-V1`. The historical receipt SHA-256 must remain
unchanged and no new mission should be created.

Do not commit until participant verification passes.
