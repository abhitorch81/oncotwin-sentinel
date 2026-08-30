# Checkpoint 4B — streaming voice and bounded navigation

This overlay replaces browser speech recognition and complete MP3 playback with a
persistent Cloud Run WebSocket. It streams 16 kHz microphone PCM to native audio and
schedules returned 24 kHz PCM chunks in one browser AudioContext.

Scientific authority remains the persisted Gemini 3.5 Google ADK mission receipt. The
native-audio transport has one bounded navigation tool and no approval or persistence
tool.

Required local environment:

```bash
export LIVE_VOICE_MODEL="gemini-3.1-flash-live-preview"
export LIVE_VOICE_LOCATION="global"
```

Verification commands and the spoken command matrix are supplied in the handoff.
