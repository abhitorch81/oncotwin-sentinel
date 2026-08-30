# Checkpoint 4C — strict Gemini 3.5+ governed voice

This repair removes the Gemini 3.1 native-audio transport. Microphone PCM is streamed
server-side to `gemini-3.5-transcribe-live`; finalized text enters the existing governed
ADK `gemini-3.5-flash` command path. Only validated agent text is rendered by Google
Cloud Text-to-Speech. No API key is exposed to the browser, and voice cannot approve or
persist a child run.

Local and production runtimes use Vertex AI Application Default Credentials. No Gemini
API key or browser credential is required. The live model is
`gemini-3.5-transcribe-live-preview` on the Vertex AI global endpoint.

Verification gate:

1. `/api/live/voice/proof` reports both Gemini models as 3.5 and the aggregate gate true.
2. Microphone state changes from connecting to listening.
3. Interim and final transcripts appear without browser speech recognition.
4. A final utterance triggers the existing ADK command route and Chirp narration.
5. Speaking while narration plays cancels playback immediately.
6. Saying `stop` never enters the mission command endpoint.
7. Voice approval remains blocked.

Repair v3 also treats WebSocket code 1000 as a clean close and coalesces finalized
transcription fragments for 700 ms before sending exactly one governed command.

Repair v4 prevents the existing scene narration from autoplaying when the microphone
opens and gates microphone upload while Chirp is speaking. A sustained near-field voice
signal still cancels playback and resumes transcription, avoiding speaker-to-microphone
self-transcription loops.
