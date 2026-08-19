#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"
GCP_ZONE="${GCP_ZONE:-asia-south1-a}"

gcloud compute ssh "${DATAHUB_VM_NAME}" \
  --project="${GCP_PROJECT_ID}" \
  --zone="${GCP_ZONE}" \
  --tunnel-through-iap \
  --command='set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y nodejs npm curl ca-certificates
# Ubuntu distro Node may be too old for current Gemini CLI / Skills CLI.
# Install an explicit compatible Node release into /usr/local via `n`.
sudo npm install -g n
sudo n 22.20.0
export PATH="/usr/local/bin:$HOME/.local/bin:$PATH"
hash -r
echo "Node: $(node --version)"
echo "npm: $(npm --version)"
if ! command -v uvx >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
sudo npm install -g @google/gemini-cli@latest
mkdir -p "$HOME/oncotwin-agent"
cd "$HOME/oncotwin-agent"
npx -y skills add datahub-project/datahub-skills -a gemini-cli -y
echo "Installed DataHub Skills:"
find .agents/skills -mindepth 1 -maxdepth 1 -type d -printf "  %f\n" | sort
echo
echo "Gemini CLI: $(gemini --version)"
echo "uvx: $HOME/.local/bin/uvx"'

cat <<'EOF'

DataHub Skills are installed on the GCP VM for Gemini CLI.

Next, SSH to the VM and configure the MCP connection with the SCOPED DataHub
service-account token. Do not paste that token into this script or Git:

  gcloud compute ssh oncotwin-datahub --zone=asia-south1-a --tunnel-through-iap
  export DATAHUB_GMS_TOKEN='PASTE_SCOPED_TOKEN_HERE'
  gemini mcp add \
    -e DATAHUB_GMS_URL='http://127.0.0.1:8080' \
    -e DATAHUB_GMS_TOKEN="$DATAHUB_GMS_TOKEN" \
    datahub "$HOME/.local/bin/uvx" mcp-server-datahub@latest

Then start `gemini`, run `/skills list`, and try:
  Find the canonical OncoTwin progression dataset and explain why it is trustworthy.
  Trace downstream impact from progression_features.
  Find quality issues that could break the progression model.

EOF
