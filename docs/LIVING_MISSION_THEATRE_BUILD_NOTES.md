# Living Mission Theatre build notes

## Checkpoint 2A — agent-directed camera choreography

- Fixed deterministic playback so the scene reads only currently visible mission events;
  it no longer jumps immediately to the final approval scene.
- Added five typed camera shots: clone R7, candidate forge, tumour core, liver sink, and
  approval boundary.
- Added eased camera and field-of-view transitions, followed by release back to manual
  orbit control.
- Added a reduced-motion path that snaps safely to each shot.
- Participant verification: local API and frontend started successfully; the updated
  mission theatre was confirmed working.

## Checkpoint 2B — agent-driven scientific scene states

- Added a pulsing R7 clone signal lock with evidence pins.
- Added holographic A/B/C forge slots for the Nano Designer stage.
- Replaced static dots with flowing distribution curves that compare tumour delivery and
  candidate B's liver route.
- Added a red liver-sink quarantine cage and breached-ceiling label.
- Added the final three-dimensional human-authority membrane.
- Increased deterministic stage dwell time so the complete sequence reads in 6–7 seconds.
- Participant verification: CORS was corrected for both local hostnames; a fresh mission
  ran against the real API without `SAFE FALLBACK`, and the scene sequence was confirmed
  working.
