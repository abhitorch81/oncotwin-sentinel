# Apply Checkpoint 3D

Checkpoint 3D persists a bounded rerun as a separate child mission with immutable lineage.
The parent is never rewritten, voice and agents cannot persist the child, and the child
requires a separate human approval.

## Validate

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
source .venv-adk/bin/activate

git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

## Visual verification

1. Start a fresh mission and select candidate B.
2. Click `PREVIEW B AT 70 NM`.
3. Confirm the preview still says `PREVIEW ONLY · NOT STORED`.
4. Click `PERSIST AS CHILD RUN · HUMAN ACTION`.
5. Confirm the evidence receipt shows `CHILD OF parent → child`.
6. Confirm the child is not approved and the approval membrane requires a new UI approval.
7. Reload and confirm the child mission and lineage restore from Firestore.

## Authority verification

The persistence endpoint accepts only the exact UI confirmation. Voice and API channels must
return `403`, and a modified preview identifier must return `400` without creating a mission.
