#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
DATAHUB_VM_NAME="${DATAHUB_VM_NAME:-oncotwin-datahub}"
GCP_ZONE="${GCP_ZONE:-asia-south1-a}"

if gcloud compute instances describe "${DATAHUB_VM_NAME}" --zone="${GCP_ZONE}" >/dev/null 2>&1; then
  echo "VM ${DATAHUB_VM_NAME} already exists."
  exit 0
fi

gcloud compute instances create "${DATAHUB_VM_NAME}" \
  --project="${GCP_PROJECT_ID}" \
  --zone="${GCP_ZONE}" \
  --machine-type=e2-standard-4 \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=oncotwin-subnet \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account="oncotwin-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --create-disk=auto-delete=yes,boot=yes,device-name="${DATAHUB_VM_NAME}",image-family=ubuntu-2404-lts-amd64,image-project=ubuntu-os-cloud,mode=rw,size=80,type=pd-balanced \
  --metadata=startup-script='#!/usr/bin/env bash
set -euxo pipefail
apt-get update
apt-get install -y ca-certificates curl python3-pip python3-venv
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo ${VERSION_CODENAME}) stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
grep -q /swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
python3 -m venv /opt/datahub-venv
/opt/datahub-venv/bin/pip install --upgrade pip acryl-datahub
/opt/datahub-venv/bin/datahub docker quickstart
'

echo "DataHub VM created without a public IP. Wait 5–10 minutes for startup."
echo "Use IAP SSH: gcloud compute ssh ${DATAHUB_VM_NAME} --zone=${GCP_ZONE} --tunnel-through-iap"
