# Secure GitHub Publishing Guide

## 1. Final local checks

From the project root:

```bash
python3 -m compileall -q backend/app
node --check frontend/assets/app.js
for script in scripts/*.sh; do bash -n "$script"; done

find . -type f -size +95M -not -path './.git/*'
git status --short 2>/dev/null || true
```

The `find` command should print nothing. Never upload `.env`, service-account JSON, proof files containing sensitive responses, tokens or approval values.

Optional credential scan:

```bash
rg -n --hidden -g '!.git/**' \
  'AIza[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{20,}|BEGIN.*PRIVATE KEY'
```

No result is expected.

## 2. Create an empty GitHub repository

On GitHub:

1. Click **New repository**.
2. Name it `oncotwin-datahub`.
3. Set visibility to **Public** for judging.
4. Do not initialize it with a README, `.gitignore` or license; this project already includes them.
5. Enable Issues if you want judges to report problems.

## 3. Publish using GitHub CLI — recommended

Install and authenticate once:

```bash
brew install gh
gh auth login
```

Choose **GitHub.com → HTTPS → Login with a web browser**. Do not paste a password into `git push`; GitHub does not support password authentication for Git operations.

Publish:

```bash
git init
git branch -M main
git add .
git commit -m "Release OncoTwin 3D V10.1 DataHub hackathon entry"

gh repo create oncotwin-datahub \
  --public \
  --source=. \
  --remote=origin \
  --push
```

## 4. Alternative: publish to an existing empty repository

```bash
git init
git branch -M main
git add .
git commit -m "Release OncoTwin 3D V10.1 DataHub hackathon entry"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/oncotwin-datahub.git
git push -u origin main
```

If authentication is requested, use `gh auth login` or a fine-grained personal access token—not your GitHub password.

## 5. Repository settings for judges

After pushing:

1. Add repository description: `DataHub-grounded 3D cancer-context agents with governed ML repair and inherited knowledge.`
2. Add topics: `datahub`, `mcp`, `agent-context-kit`, `ai-agents`, `mlops`, `bioinformatics`, `single-cell`, `threejs`, `bigquery`, `google-cloud`.
3. Add the Cloud Run URL under **About → Website**.
4. Pin the repository on your GitHub profile.
5. Confirm the Actions tab shows a green CI run.
6. Create a release named `OncoTwin V10.1 — Hackathon Submission` and attach the source ZIP plus machine-readable proof files.

## 6. Add screenshots without leaking data

Create `docs/screenshots/` and add:

- `01-live-mission.png`
- `02-active-datahub-incident.png`
- `03-downstream-lineage.png`
- `04-model-blocked.png`
- `05-generated-repair.png`
- `06-validation-pass.png`
- `07-inherited-knowledge.png`
- `08-proof-galaxy.png`

Crop browser tabs, terminal history, project billing details, tokens and approval fields.

## 7. Final public-repository test

Use a clean directory:

```bash
cd /tmp
git clone https://github.com/YOUR_GITHUB_USERNAME/oncotwin-datahub.git oncotwin-judge-test
cd oncotwin-judge-test
bash scripts/12_local_demo.sh
```

This confirms the repository works for someone who does not have your original development directory.

