# Google Cloud production deployment

OncoTwin uses independent Cloud Run services for the React 3D theatre and FastAPI mission API, a dedicated user-managed runtime identity, Vertex AI for Gemini/ADK, and Firestore Native mode for persistent mission memory.

## Deploy

Run from the repository root:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
bash infra/gcp/deploy.sh
```

The script enables the required APIs, creates the Artifact Registry repository and least-privilege runtime service account, builds commit-tagged images, deploys both services with HTTP startup/liveness probes, wires production CORS, and fails unless the public health and Firestore persistence proofs pass.

The runtime uses Application Default Credentials through the Cloud Run service identity. Do not upload service-account keys or set `GOOGLE_APPLICATION_CREDENTIALS` in Cloud Run.

## Runtime permissions

- `roles/datastore.user`
- `roles/aiplatform.user`

Secret Manager is enabled for the forthcoming receipt-signing and Gemini Live session-secret slice; no placeholder secret is granted to the runtime.
