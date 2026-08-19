# Milestone 1 validation

Validation is performed before packaging. Expected checks:

- Python source compiles.
- Eleven deterministic mission, simulation, memory, and approval-policy tests pass.
- Candidate B is rejected and exactly one candidate is preferred.
- Voice cannot approve; explicit UI confirmation can.
- JSON contracts and frontend package metadata parse.
- Repository contains no AWS/Lambda source references.

Frontend dependency installation/build requires network access and should be repeated in the target repository with `npm install && npm run build`.

## Packaged baseline result

- `python3 -m compileall -q apps/api/app`: passed
- `python3 -m unittest discover -s apps/api/tests -v`: 11 passed
- JSON package and mission contract parsing: passed
- Google Cloud deployment shell syntax: passed
- Forbidden cloud SDK scan (`aws_`, `boto3`, `amazonaws`, `bedrock`, `sagemaker`): clear
- FastAPI runtime smoke test: deferred until requirements are installed
- Frontend TypeScript/Vite production build: deferred until npm dependencies are installed
