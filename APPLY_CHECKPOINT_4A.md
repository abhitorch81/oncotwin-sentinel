# Apply Checkpoint 4A — Gemini Live duplex voice

This overlay adds real bidirectional Gemini Live audio without changing the human approval
or child-receipt persistence boundaries.

## Verify

```bash
source .venv-adk/bin/activate
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

## Local API environment

Keep the existing Gemini 3.5 ADK configuration and add the Live model:

```bash
export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_CLOUD_PROJECT="project-1f5f7d56-1029-4c78-a68"
export GOOGLE_CLOUD_LOCATION="global"
export GEMINI_MODEL="gemini-3.5-flash"
export ADK_MODEL="gemini-3.5-flash"
export GEMINI_LIVE_ENABLED="true"
export GEMINI_LIVE_MODEL="gemini-3.1-flash-live-preview"
export FIRESTORE_ENABLED="true"
export FIRESTORE_DATABASE="(default)"
export ADK_ENABLED="true"
export ALLOWED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"
```

Start Uvicorn on port 8000 and Vite on port 5173 as in the earlier checkpoints. The first
microphone click requires browser permission.

## Visual gate

1. Run or restore a successful mission and select candidate B.
2. Click the microphone and wait for `GEMINI LIVE · LISTENING`.
3. Say, “Why was candidate B rejected?”
4. Confirm the transcript enters the bounded command path and Gemini speaks the explanation.
5. Interrupt the spoken answer with, “Stop. Show me the liver value at eighteen hours.”
6. Confirm playback stops immediately and the next bounded explanation focuses T+18H.
7. Say, “Approve it.” Confirm Gemini says human UI confirmation is required and the mission
   approval state does not change.
8. Confirm `/api/live/voice/proof` reports `credentials_exposed: false`,
   `voice_can_approve: false`, and `voice_can_persist_child_run: false`.

The next checkpoint is synthetic image evidence upload and grounded comparison against prior
Firestore mission receipts.
