# Checkpoint 4D — Gemini 3.5 synthetic image evidence

This checkpoint completes the multimodal loop with a bounded synthetic-image upload. Gemini
3.5 Flash analyzes the image using selected candidate/time context and privacy-safe Firestore
receipt summaries. Raw image bytes are never persisted.

Verification:

```bash
source .venv-adk/bin/activate
pip install -r apps/api/requirements.txt
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

Participant visual gate:

1. Start a fresh mission and select candidate B at T+18H.
2. Upload a synthetic PNG/JPEG/WebP image no larger than 5 MB.
3. Confirm the card reports Gemini 3.5, selected context, receipt comparisons and SHA-256.
4. Confirm the R7 scene focuses and governed voice reads the result.
5. Confirm Firestore proof includes `image_evidence` and the card says raw image not stored.
6. Try a text file renamed `.png`; the API must reject it.
