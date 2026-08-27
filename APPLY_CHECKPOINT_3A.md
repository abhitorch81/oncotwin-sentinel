# Apply Living Mission Theatre — Checkpoint 3A

This overlay adds a receipt-driven 0–24 hour synthetic simulation scrubber. It assumes
the final checkpoint 2D overlay is already applied on `feature/living-mission-theatre`.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3A.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart the API because the mission receipt now includes 75 temporal frames: 25 hourly
snapshots for each of three candidates. Run a **fresh** Nano Safety Mission; a mission
restored from Firestore may use the compatible frontend fallback timeline.

Verify visually:

1. A new `T+00H` to `T+24H` timeline appears above the final candidate cards.
2. Dragging the scrubber changes tumour, liver, and kidney values in all three cards and
   in the selected-candidate inspector.
3. Nanoparticle positions advance along their three-dimensional delivery paths as time
   increases; tumour glow and liver/kidney ghost intensity evolve with the receipt.
4. Candidate B changes from `RISK RISING` to `QUARANTINED` only after its synthetic liver
   accumulation crosses the 45% policy ceiling. The timeline labels the crossing hour.
5. The play button runs from hour 0 through hour 24 and stops. Dragging the slider pauses
   playback immediately.
6. Candidate selection, orbit controls, ADK trace, Firestore evidence, and human approval
   still work, with no browser-console errors.

All curves are deterministic synthetic kinetics for a research demonstration, not
clinical pharmacokinetic predictions.
