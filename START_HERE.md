# Start the clean build in your repository

From your existing `oncotwin-sentinel` repository on the Mac:

```bash
git status --short
git tag -a v12-safety-baseline -m "Safety-reviewed pre-rebuild baseline"
git push origin v12-safety-baseline
git switch -c rewrite/google-native-core
```

Extract this Milestone 1 bundle into a **separate temporary directory first**. Review it, then copy its contents into the repository. Because the intended result is a controlled replacement, do not delete the old tree until the safety tag is visible on GitHub.

Recommended first verification after copying:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
make check

cd apps/web
npm install
npm run build
cd ../..

git status --short
git diff --check
git add .
git commit -m "feat: establish Google-native Living Evidence baseline"
git push -u origin rewrite/google-native-core
```

Run the API and web app using the two-terminal instructions in `README.md`. Do not merge to `main` until the frontend build, mission flow, approval denial, and local demo fallback have all been observed.

