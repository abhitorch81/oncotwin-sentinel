# Slice 4.1G — Firestore Mission Memory

OncoTwin uses Firestore Native mode as invisible operational memory for the Nano Safety
Mission. It does not expose a standalone database screen. Evidence Scout simply retrieves
relevant prior receipt hashes, the mission can be reconstructed after restart, and human
approval is written as an immutable audit event.

## Collections

- `missions`: complete bounded mission state plus `resume_cursor`.
- `mission_receipts`: simulation result and SHA-256 evidence receipt.
- `approval_events`: immutable human approval decisions.

Mission and receipt writes use a Firestore write batch. Approval updates use a Firestore
transaction with a deterministic audit-event ID, making retries idempotent.

## Local authentication

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export FIRESTORE_ENABLED=true
export FIRESTORE_DATABASE='(default)'
```

Create a Firestore **Native mode** database in the Google Cloud console before enabling
the adapter. Database location is permanent, so choose the location deliberately.

## Verify persistence across processes

```bash
python3 scripts/verify_firestore_memory.py write
python3 scripts/verify_firestore_memory.py read nano-REPLACE_ME
python3 scripts/verify_firestore_memory.py proof
```

The read command starts a new Python process and succeeds only when the mission was
reconstructed from Firestore.

## Cloud Run identity

Use a dedicated Cloud Run service account. Grant it `roles/datastore.user`; do not ship a
service-account key or set `GOOGLE_APPLICATION_CREDENTIALS` in Cloud Run.

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:oncotwin-api@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

Configure these Cloud Run environment variables:

```text
FIRESTORE_ENABLED=true
FIRESTORE_DATABASE=(default)
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

## Judge proof

```bash
curl -s http://127.0.0.1:8000/api/memory/proof | python3 -m json.tool
```

A live persistent result reports `firestore` for both backend fields, `persistent=true`,
`healthy=true`, and `degraded=false`. Demo fallback is always labeled non-persistent.
