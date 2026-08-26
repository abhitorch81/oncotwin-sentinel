# Apply Living Mission Theatre — Checkpoint 2C

This overlay adds scientifically differentiated, selectable synthetic candidate bodies.
It assumes checkpoint 2B is committed on `feature/living-mission-theatre`.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_2C.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Run a fresh Nano Safety Mission and verify:

1. Aster-48 is the smallest cyan particle, with a smooth core and stealth shell.
2. Brimstone-92 is the largest red particle, with a faceted core and positive-charge
   spike cues.
3. Calyx-61 is medium-sized and green, with visible ligand stems and receptor nodes.
4. Selecting any 3D body adds a focus ring and opens an inspector showing the exact
   receipt values for size, charge, ligand, stealth, tumour delivery, and liver risk.
5. The final A/B/C comparison cards remain selectable after the 3D forge stage.
6. B is visibly quarantined and C visibly preferred after the Safety Steward decision.

These are synthetic parameter visualizations, not molecular structures or medical claims.
