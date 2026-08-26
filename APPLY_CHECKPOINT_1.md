# Apply Living Mission Theatre — Checkpoint 1

From the OncoTwin repository on your Mac:

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_1.zip -d .

source .venv-adk/bin/activate
python -m compileall -q apps/api/app
python -m pytest -q
npm --prefix apps/web run build
git diff --check
git status --short
```

Expected outcomes:

- 30 or more Python tests pass.
- Vite completes the production build.
- `git diff --check` prints nothing.
- The status contains only the checkpoint source changes you intend to commit.

Start the API and web app using the same environment and commands already used by the
Cloud Run production branch. Run a fresh Nano Safety Mission. Each agent card should show
a specific work product, exact metrics, confidence/evidence information, and an active
work-product card over the theatre.

Do not commit `.env.memorymesh.local`. If it has ever been pushed to a public repository,
remove it from tracking and rotate every credential it contained.
