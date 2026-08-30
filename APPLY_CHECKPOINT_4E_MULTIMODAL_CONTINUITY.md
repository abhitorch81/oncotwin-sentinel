# Checkpoint 4E — image-grounded follow-up and modality trace

Apply only after Checkpoint 4D. Gemini 3.5 Flash and Google ADK remain the sole scientific
reasoning workflow. This checkpoint adds continuity and provenance without another model.

```bash
source .venv-adk/bin/activate
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

Visual gate:

1. Select B at T+18H and upload a synthetic image.
2. Confirm the right-rail trace displays image → Gemini 3.5/ADK → evidence ID → B/T+18H → Firestore.
3. Ask “How does this image affect candidate B?” by text and voice.
4. Confirm the answer cites the same IMG identifier and says the stored receipt is unchanged.
5. Confirm the trace never overlaps the fixed microphone or command controls.
