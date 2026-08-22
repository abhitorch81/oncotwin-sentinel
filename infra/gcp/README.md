# Google Cloud deployment foundation

Milestone 3 supplies independent Cloud Run containers for the web theatre and mission API,
Google ADK execution, and Firestore mission memory. Before production, connect Secret
Manager values with `--set-secrets`, grant the API service identity
`roles/datastore.user`, and add Gemini Live behind the existing voice boundary.

The deployment script is intentionally explicit and contains no AWS resources. Run from the repository root after `gcloud auth login` and setting `GOOGLE_CLOUD_PROJECT`.

Note: Cloud Build argument injection for the Vite build should be finalized in Milestone 2 with a checked-in `cloudbuild.yaml`; the current script is an infrastructure foundation, not yet a production release claim.
