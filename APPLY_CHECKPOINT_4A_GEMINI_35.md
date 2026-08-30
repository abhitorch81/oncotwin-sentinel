# Checkpoint 4A — governed Gemini 3.5 voice

This replacement removes the unverified Live-model WebSocket path. Gemini 3.5 Flash through
Vertex AI remains the sole reasoning engine; Chrome only captures commands and speaks the
validated agent response.

The final repair uses Google Cloud Text-to-Speech with the Chirp 3 HD Charon voice for
presentation-quality audio. It is a renderer only; it does not reason or replace Gemini 3.5.

After applying the overlay, remove the obsolete hook if it exists:

```bash
rm -f apps/web/src/hooks/useGeminiLiveVoice.ts
```

Verify:

```bash
source .venv-adk/bin/activate
pip install -r apps/api/requirements.txt
git restore apps/web/tsconfig.tsbuildinfo
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```

Start the API using the existing Gemini 3.5 environment plus:

```bash
export GOVERNED_VOICE_ENABLED="true"
```

Enable the renderer once in the Google Cloud project:

```bash
gcloud services enable texttospeech.googleapis.com \
  --project project-1f5f7d56-1029-4c78-a68
```

Do not set `GEMINI_LIVE_MODEL` or `GEMINI_LIVE_ENABLED`.

In Chrome, run a successful mission, click the microphone, speak a candidate question and
allow the validated response to be narrated. Click the microphone while it is speaking to
cancel playback and issue another command. Typed `stop` must stop audio without becoming a
mission question. Spoken or typed `approve it` must produce an authority refusal without
changing the mission approval state.
