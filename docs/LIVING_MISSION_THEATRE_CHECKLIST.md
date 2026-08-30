# Living Mission Theatre build checkpoints

The hero flow remains the governed Nano Safety Mission. The four visible Google ADK agents
must produce concrete, inspectable work products and mutate the same 3D scientific scene.

## Checkpoint 1 — agent work products and scene contracts

- [x] Evidence Scout emits clone signals, confidence, evidence IDs, and memory count.
- [x] Nano Designer emits three bounded candidate blueprints with exact parameters.
- [x] Twin Simulator emits a 24-hour tumour/liver/kidney comparison.
- [x] Safety Steward emits the rejected candidate, breached threshold, and preferred option.
- [x] Human approval remains an explicit blocked autonomy boundary.
- [x] Live ADK and deterministic fallback share one typed artifact/scene-patch contract.
- [x] Work products are visible in the agent rail and in-scene status card.

Verification gate:

```bash
python -m compileall -q apps/api/app
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

## Checkpoint 2 — evolving 3D theatre

- [x] Choreograph the camera by `camera_target` rather than one static composition.
- [x] Add clone isolation, candidate forge, distribution paths, quarantine, and approval overlays.
- [x] Make candidate A/B/C geometries scientifically distinct and selectable.
- [x] Keep stable frame rate and reduced-motion fallback.

## Checkpoint 3 — direct scientific interaction

- [x] Add a 0–24 hour simulation scrubber.
- [x] Let users inspect candidates and ask why a candidate was rejected.
- [x] Support bounded reruns such as “reduce particle size and rerun.”
- [x] Persist privacy-safe ADK traces across Cloud Run instances and scale-to-zero.
- [x] Store child-run receipts and parent mission lineage in Firestore.
- [x] Run and preserve a production ADK trace using Gemini 3.5 Flash through Vertex AI.

## Checkpoint 4 — Gemini 3.5 multimodal control

- [x] Provide governed Gemini 3.5 transcription, seamless Chirp narration, stop/barge-in,
      and repeatable follow-up turns.
- [x] Synchronize spoken explanations with selected 3D objects and agent work products.
- [x] Support bounded voice navigation: next/previous candidate, candidate selection,
      next/previous/set hour, play/pause timeline, and approval-boundary focus.
- [ ] Support synthetic evidence upload and grounded comparison against prior missions.
- [x] Prove voice cannot approve a mission.
- [ ] Checkpoint 4E: verify image-grounded voice/text follow-ups and the visible modality trace.

## Later mission expansion

After the Nano Safety Mission is polished and reproducible, reuse the theatre contract for
four to six additional missions. Do not expose more agents; change their tools, artifacts,
scene patches, and policy envelope per mission.
- [x] Checkpoint 4C: verify Gemini 3.5 Live transcription, ADK 3.5 response, Chirp playback, barge-in, and voice authority denial.
- [ ] Checkpoint 4F: expose real ADK handoffs, replayable work products, the receipt decision chain and measurable mission impact.
