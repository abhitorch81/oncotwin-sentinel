# Apply Living Mission Theatre — Checkpoint 3A repair

This focused overlay repairs the three issues found during participant verification of
Checkpoint 3A. It assumes the original Checkpoint 3A overlay is already applied.

- Adaptive sparkle buffers are remounted whenever render quality changes, preventing a
  draw count from exceeding the allocated GPU buffer.
- A restored mission reloads its saved ADK trace, so a successful run remains visibly
  `GEMINI · VERIFIED` rather than degrading to `LOCAL TRACE` after refresh.
- The Evidence Scout live trace receives the actual count of prior receipt hashes already
  retrieved for the mission instead of displaying a hard-coded zero.

Apply and validate:

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3A_Repair.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart the API with Google Cloud model authentication enabled and restart the frontend.
Clear the active mission, run one fresh mission, and verify:

1. The browser console remains free of `GL_INVALID_OPERATION` errors while adaptive
   quality changes.
2. The mission completes with `GEMINI · VERIFIED` and remains verified after reload.
3. The header shows `FIRESTORE LIVE` and the footer shows the persistent mission count.
4. Evidence Scout reports at least one prior receipt when Firestore already contains
   earlier receipts.
5. The 0–24 hour timeline, candidate selection, and human approval boundary still work.

Do not commit until this visual verification passes.
