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

## Checkpoint 2C — selectable candidate bodies

- Added receipt-synchronized synthetic visual models with relative 48/92/61 nm scale.
- Represented A with a smooth stealth shell, B with a large faceted cationic/spike cue,
  and C with ligand stems and receptor nodes.
- Added pointer selection, focus rings, B quarantine state, and C preferred state.
- Added a shared inspector driven by the mission receipt rather than duplicated display
  constants.
- Made the final comparison cards selectable so inspection remains available after the
  short forge stage.
- Participant verification: the local production build and live mission interaction were
  confirmed working.

## Checkpoint 2D — adaptive rendering and safe motion

- Added runtime quality monitoring that adapts pixel density and background sparkle count.
- Added high, balanced, and conservative renderer profiles with a visible footer status.
- Added a reactive reduced-motion path that stops pulsing, floating, particle-flow,
  tumour-spin, quarantine-spin, and approval-boundary animations.
- Preserved candidate selection, manual orbit controls, receipts, and approval controls in
  reduced-motion mode.
- Added WebGL initialization and context-loss safe-mode messaging without hiding the
  non-3D evidence interface.
- Participant verification: 30 backend tests passed, the frontend production build passed
  after correcting the CameraDirector prop binding, and the updated application was
  confirmed working.

## Checkpoint 3A — receipt-driven temporal simulation

- Remounts the adaptive sparkle geometry whenever quality changes so GPU draw counts and
  allocated buffers stay synchronized.
- Restores the persisted ADK trace with a Firestore mission, preserving the truthful
  `GEMINI · VERIFIED` provenance badge after a browser reload.
- Passes the mission's actual prior-receipt count into the live Evidence Scout artifact.
- Adds an immediate launch lock after verification exposed duplicate mission POSTs from
  rapid UI interaction, avoiding concurrent ADK runs and misleading gRPC fork warnings.
- Participant verification completed: 32 backend tests passed; the TypeScript/Vite
  production build passed; one launch created one ADK mission; the trace completed all
  four agents with no fallback; Evidence Scout recovered three prior Firestore receipts;
  and the browser console remained free of WebGL errors while the timeline rendered.
