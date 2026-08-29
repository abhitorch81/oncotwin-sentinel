# Checkpoint 4C v5 — deterministic stop and barge-in repair

This repair keeps a short microphone pre-roll while Chirp is speaking so Gemini 3.5
receives the complete interruption instead of losing the first syllable. Two sustained
near-field frames interrupt playback, cancel any pending command, notify the server, and
resume transcription. The speaking-state UI control now stops only the current narration
and keeps the voice session listening.

Verification:

1. Open voice and ask why candidate B was rejected.
2. While the response is speaking, say `stop` once at normal near-field volume.
3. Playback must stop within a fraction of a second and the session must remain listening.
4. No `/commands` request may be created for `stop`.
5. Ask a follow-up without reopening the microphone.
6. Repeat using the square control; it must stop speech without closing voice.
