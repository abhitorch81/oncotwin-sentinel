# Gemini Live voice lane

OncoTwin Sentinel uses a backend WebSocket bridge at `/api/agentic/live`.
Browser audio is converted to raw 16-bit PCM at 16 kHz, forwarded through the
official Google Gen AI SDK, and played as 24 kHz PCM native audio. Input and
output transcriptions remain visible in the command center.

## Safety architecture

Gemini is a conversational voice, not an action authority. Every finalized
input transcript is sent through the same deterministic `route_agentic_command`
function used by typed commands. Gemini receives no mutation tools, no approval
secret, and no browser credential. An approval utterance can only open the
visible human review panel.

If Live is disabled, misconfigured, unavailable or disconnected, the UI keeps
the Phase 2 browser-speech plus deterministic-router fallback.

## Local configuration

Add these values to `.env` without committing the file:

```dotenv
GEMINI_LIVE_ENABLED=true
GEMINI_LIVE_USE_VERTEXAI=false
GEMINI_LIVE_MODEL=gemini-3.1-flash-live-preview
GEMINI_LIVE_VOICE=Kore
GOOGLE_API_KEY=replace-with-your-server-only-key
```

Then restart Uvicorn. `/api/agentic/capabilities` should report
`lanes.gemini_live.status` as `ready`.

For Vertex AI, set `GEMINI_LIVE_USE_VERTEXAI=true`, configure
`GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`, and use a Live model that is
available to that project. Cloud Run uses its service-account Application
Default Credentials; do not provide a JSON key to the browser.

## Judge flow

1. Use headphones to reduce speaker-to-microphone echo.
2. Tap the microphone; the badge changes to `GEMINI LIVE · READY` and the panel
   enters the live state.
3. Say: “Show me why the resistant clone is red.”
4. The native voice responds while the deterministic router focuses the actual
   Three.js clone and exposes the color evidence.
5. Interrupt the response with another question to demonstrate barge-in.
6. Say: “Approve and execute the writeback.” The interface may open the review
   gate, but it must never click approval or perform a mutation.

Live audio sessions are capped at 14 minutes in OncoTwin so the browser can
rotate the connection before the provider's normal audio-only session limit.
