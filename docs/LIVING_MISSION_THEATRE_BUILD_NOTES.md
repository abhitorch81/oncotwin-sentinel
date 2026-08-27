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

## Checkpoint 3B — contextual candidate explanation

- Adds a receipt-grounded `/commands` response tied to selected candidate and simulation
  hour instead of starting another mission.
- Safety Steward explanations expose policy threshold, breach hour, current/final organ
  accumulation, evidence IDs, receipt provenance and a future Gemini Live `spoken_text`.
- A contextual scene patch focuses the exact 3D evidence and updates the scrubber hour.
- Autonomous approval remains false; browser voice output is intentionally deferred to
  the Gemini Live checkpoint.
- Participant verification exposed restored Firestore missions created before Checkpoint
  3A with no stored timeline. The command service now reconstructs the same deterministic
  hourly kinetics in memory without rewriting or rehashing the legacy receipt.
- Visual review exposed the candidate inspector covering the contextual evidence card.
  The explanation now becomes the single active inspection panel, and its close control
  restores the selected candidate inspector without clearing scene selection.
- Participant verification completed: B selected the liver-sink camera, moved the receipt
  timeline to T+18H, displayed the 46% first breach against the 45% ceiling and the 68%
  T+24H value, exposed policy/simulation receipt provenance without panel overlap, and
  preserved the human-authority boundary.

## Checkpoint 3C — bounded rerun preview

- Adds a typed `bounded_rerun` command path for explicit particle sizes inside the
  35–120 nm synthetic research envelope.
- Recomputes all candidates and all 75 temporal frames while leaving the parent Firestore
  receipt, receipt hash, and approval state untouched.
- Drives the same 3D particle bodies, timeline, comparison cards and organ-risk scene from
  preview results; B visibly contracts from 92 nm to 70 nm.
- B at 70 nm improves tumour payload from 49% to 61%, but liver accumulation only falls
  from 68% to 66%, so the simulator truthfully keeps it rejected.
- Returns `persisted: false`, `lineage_status: preview_only`, and `approval_granted: false`;
  persisted parent/child receipt lineage remains Checkpoint 3D.
- Participant verification completed: Brimstone-70 rendered with a visibly smaller body,
  61% tumour payload and 66% liver accumulation while remaining rejected. The first
  liver-ceiling breach moved from T+18H to T+19H, the panel remained explicitly
  `PREVIEW ONLY · NOT STORED`, and the original Firestore receipt and stored-mission count
  remained unchanged.

## Production repair — durable ADK traces

- Production mission `nano-efe5210fd8` exposed that missions survived in Firestore while
  `/adk-trace` returned `ADK trace not initialized` and `/adk-events` remained `queued`.
- Root cause: the sanitized ADK trace repository was process-local, so a different Cloud
  Run instance or scale-to-zero could retrieve the mission but not its agent execution.
- Adds an `adk_traces` Firestore collection for queued, running, succeeded and fallback
  states plus privacy-safe translated agent events.
- The persisted contract excludes prompts, raw model output, tool arguments, credentials
  and model reasoning. Local/demo operation retains the in-memory repository.
- Health, architecture and memory proofs now report the configured trace backend.
- Participant verification completed: 42 backend tests and the frontend production build
  passed. Mission `nano-11f4dfd2dc` remained available after the API process restarted,
  returned `status: succeeded`, retained 12 translated events across all four visible
  agents, reported `model_call_executed: true`, and had no fallback reason.

## Checkpoint 3D — persisted child-run lineage

- Adds an explicit UI-only authority endpoint that rebuilds and verifies a bounded preview
  server-side before creating a child mission.
- Uses a deterministic child identifier so retries are idempotent and cannot create duplicate
  receipts from the same preview.
- Stores parent/root mission IDs, preview provenance, the exact parameter change, actor and
  persistence channel with the child mission and its new immutable receipt hash.
- Leaves the parent receipt and approval state untouched; every child starts at
  `awaiting_human_approval` and requires its own approval event.
- Rejects voice/API persistence, missing confirmation and tampered preview identifiers before
  any repository write.
- Adds a parent→child lineage row to the evidence receipt and a visible human-persisted child
  state in the 3D theatre.
- Participant verification completed: candidate B was persisted as a 70 nm child mission;
  the evidence receipt displayed the parent and child IDs plus the exact 92→70 nm change;
  Firestore reported the child among 37 stored missions; and the authority membrane remained
  paused with `REVIEW & APPROVE`, proving the child inherited no parent approval.

## Checkpoint 3E — Google eligibility upgrade

- Changes all runtime and Cloud Run deployment defaults from `gemini-2.5-flash` to the
  stable `gemini-3.5-flash` model through Vertex AI in the global location.
- Adds a fail-closed semantic version gate so an older or unversioned Gemini alias cannot
  be presented as satisfying the Gemini 3.5 requirement.
- Adds `/api/eligibility/proof`, reporting the configured Gemini model/access path, Google
  ADK version/workflow, and Cloud Run/Firestore infrastructure without triggering a model
  call or exposing project credentials.
- Extends deployment verification to fail unless Gemini 3.5+, Vertex AI, Google ADK and at
  least one Google Cloud infrastructure service are all truthfully configured.
- Preserves older trace files as historical evidence; only a new production mission may
  supply the final `model_call_executed: true` Gemini 3.5 proof.
- Participant verification completed: 49 backend tests and the TypeScript/Vite production
  build passed. Cloud Run release `abc3087` deployed API revision
  `oncotwin-agentic-api-00008-qqf` and web revision `oncotwin-agentic-web-00004-mzn` at
  100% traffic. Production eligibility reported Gemini 3.5 Flash through Vertex AI,
  Google ADK 2.8.0, Cloud Run and Firestore with `requirements_met: true`.
- Production mission `nano-2c99e4c2cb` completed the four-agent `ADK2GraphWorkflow` with
  model `gemini-3.5-flash`, 12 privacy-safe events, `model_call_executed: true`, and no
  fallback reason.
