# Security Policy

## Research-only boundary

OncoTwin is a hackathon research demonstration using synthetic/de-identified concepts. It is not a medical device and must not be used for diagnosis, treatment selection or patient care.

## Credentials

Never commit:

- DataHub access tokens
- `WRITEBACK_APPROVAL_SECRET`
- Google API keys
- service-account JSON keys
- `.env` files

Use Google Secret Manager for deployed credentials and environment variables only for a local shell. The browser never receives DataHub tokens, the approval secret or the Gemini API key.

If a credential is accidentally committed, revoke it first, then remove it from Git history. Deleting it only from the latest commit is insufficient.

## Authorization model

- MCP context reads use a scoped DataHub token.
- Incident resolution and metadata writeback use a separate server-only administrator token.
- BigQuery repair requires the Cloud Run service account and a human approval value.
- Failed validation leaves the incident active and model consumption blocked.
- Gemini Live has no mutation tools, approval secret or clinical-action authority. Its transcript is independently interpreted by the deterministic command router, and voice can only open the visible approval panel.

## Reporting

Open a private GitHub security advisory for vulnerabilities. Do not include real patient data, access tokens or secret values in an issue.
