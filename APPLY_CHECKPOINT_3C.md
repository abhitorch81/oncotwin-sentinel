# Apply Living Mission Theatre — Checkpoint 3C

This overlay adds a bounded, non-persistent rerun preview. Selecting B and requesting
`Reduce candidate B to 70 nm and rerun` recomputes the deterministic comparison and all
75 timeline frames without modifying the original Firestore receipt or approval.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3C.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart both servers, restore or run a mission, select candidate B, and click
`PREVIEW B AT 70 NM`.

Verify:

1. The panel says `BOUNDED PREVIEW`, `PREVIEW ONLY`, and `NOT STORED`.
2. B changes from Brimstone-92 to Brimstone-70 and its 3D body becomes visibly smaller.
3. T+24H tumour payload changes from 49% to 61%; liver changes from 68% to 66%.
4. B remains rejected because 66% still exceeds the 45% policy ceiling.
5. Scrubbing 0–24H uses the preview frames.
6. Closing the preview restores the original 92 nm receipt values.
7. No new mission appears in Firestore and the approval boundary is unchanged.
8. A request outside 35–120 nm is rejected with a clear API error.

Do not commit until participant visual verification passes.
