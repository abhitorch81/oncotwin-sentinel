# OncoTwin MemoryMesh: Gemini + AWS Lambda

This extension removes Amazon Bedrock from the critical path while preserving a
meaningful AWS deployment:

1. The FastAPI API requests an embedding or semantic search.
2. An AWS Lambda container executes the memory workflow.
3. Google Gemini `gemini-embedding-001` generates a 1024-dimensional vector.
4. Lambda writes/searches that vector in CockroachDB's distributed vector index.

Only synthetic, research-only patient records are accepted by the Lambda worker.

## 1. Apply the installer

From the repository root:

```bash
python3 oncotwin_add_lambda_gemini_memory.py
python -m pip install -r requirements.txt
```

## 2. Deploy the worker

Docker Desktop must be running. Ensure `DATABASE_URL` and `GEMINI_API_KEY` are
available in the shell, or the script will prompt for them without echoing.

```bash
bash scripts/deploy_lambda_memory_vectorizer.sh
```

The deployment creates paid-capable AWS resources only after an explicit `y`
confirmation: ECR, Lambda, Secrets Manager, and CloudWatch Logs. It creates
`.env.memorymesh.local` with mode 600. Never commit that file.

## 3. Run the backend

```bash
set -a
source .env.memorymesh.local
set +a
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep `DATABASE_URL` configured in the backend shell as before.

## 4. Verify the integration

```bash
curl -s -X POST http://127.0.0.1:8000/api/memory/vectorizer/health | python3 -m json.tool

curl -s -X POST \
  http://127.0.0.1:8000/api/memory/memories/30000000-0000-0000-0000-000000000001/embed \
  | python3 -m json.tool

curl -s -X POST \
  http://127.0.0.1:8000/api/memory/patients/ONCO-007/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"What resistance mechanism is emerging?","limit":5}' \
  | python3 -m json.tool

curl -s http://127.0.0.1:8000/api/memory/patients/ONCO-007 | python3 -m json.tool
```

The final patient response should show `"embedded": true`.

## Security notes

- Do not use real patient data. The worker rejects records without
  `metadata.research_only=true`.
- The Function URL is protected by a high-entropy application token. Rotate it
  before a public demo if it is exposed.
- Database and Gemini credentials are stored in AWS Secrets Manager, not in the
  Lambda image.
- Replace root deployment access with a least-privilege IAM deployment identity.
