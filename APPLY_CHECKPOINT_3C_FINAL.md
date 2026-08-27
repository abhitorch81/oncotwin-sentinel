# Apply Living Mission Theatre — Checkpoint 3C Final

This final overlay records participant verification for the bounded rerun preview and
reapplies the complete Checkpoint 3C implementation. The preview changes the live 3D
simulation without modifying the original Firestore receipt or granting approval.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3C_Final.zip -d .

source .venv-adk/bin/activate
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Verified behavior:

1. Candidate B changes from 92 nm to 70 nm and becomes visibly smaller.
2. T+24H tumour payload changes from 49% to 61%.
3. T+24H liver accumulation changes from 68% to 66%.
4. The first liver-ceiling breach shifts from T+18H to T+19H.
5. B remains rejected against the 45% synthetic policy ceiling.
6. The preview is explicitly marked `PREVIEW ONLY · NOT STORED`.
7. The parent Firestore receipt, mission count and approval state remain unchanged.

Checkpoint 3C may be committed after applying this final overlay.
