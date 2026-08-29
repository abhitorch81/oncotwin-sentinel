# Checkpoint 4C v7 — bounded voice navigation repair

Strict Gemini 3.5 Live Transcription emits text, not the navigation tool events produced
by the removed Gemini 3.1 conversational transport. This repair maps a small, explicit
navigation vocabulary from finalized Gemini 3.5 transcripts into existing UI actions.
Navigation never reaches the scientific command endpoint and has no approval or
persistence authority.

Supported phrases include:

- `show candidate C`, `next candidate`, `previous candidate`
- `next hour`, `previous hour`, `go to T plus 18 hours`
- `play timeline`, `pause timeline`
- `show approval boundary`

Each successful action mutates the visible 3D/timeline context and produces one short,
validated spoken confirmation.
