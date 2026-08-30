# Checkpoint 4A microphone barge-in repair

This repair keeps Chrome speech recognition active while governed narration plays.
During playback, non-stop transcripts are ignored to prevent speaker echo from becoming
a new agent command. `Stop`, `stop speaking`, `be quiet`, and `cancel` immediately pause
the active audio element without calling Gemini or changing approval state.

The v2 repair detects stop phrases in interim transcript suffixes and treats Chrome's
normal `no-speech`/`aborted` events as restartable recognition lifecycle events.

The v3 repair adds microphone-level voice activity detection with browser echo
cancellation. Any human speech during playback interrupts audio immediately, so the
recognizer can capture `Stop` or a follow-up without competing with the speaker. Spoken
briefings are capped at two short sentences / 420 characters; the complete answer stays
visible in the interface.

Verify by starting voice mode, asking a question, and saying `Stop speaking` while the
response is audible. The audio must stop before transcription finalizes and the UI must
return to `LISTENING`.
