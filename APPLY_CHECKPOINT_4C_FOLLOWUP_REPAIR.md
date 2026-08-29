# Checkpoint 4C v6 — repeated follow-up narration repair

The governed command route may return the same receipt-grounded narration for a repeated
question. Text equality is not a reliable turn identifier, so every successful voice
response now increments a narration revision. The voice renderer speaks each completed
turn once, including an identical question repeated after interruption, while opening a
voice session still suppresses stale scene narration.

Verification:

1. Ask `Why was candidate B rejected?` and allow speech to begin.
2. Say `stop`; playback must stop and voice must remain listening.
3. Ask the identical question again without reopening voice.
4. Exactly one command request must return 200 and exactly one new spoken response must play.
5. Repeat once with a different follow-up question to confirm ordinary turns still work.
