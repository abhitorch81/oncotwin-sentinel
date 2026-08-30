# Checkpoint 4F — Agent Collaboration and Decision Story

This frontend-only checkpoint makes the existing governed workflow easier to understand and inspect. It does not add a model or synthesize agent dialogue.

## Adds

- A persistent mission brief: problem, objective, safety guardrail and human authority.
- A handoff ribbon generated from real visible ADK events.
- Replay controls on completed agent work products.
- Scene, candidate and simulation-time replay from each event's typed scene patch.
- A receipt-derived decision chain and measurable mission impact summary.

## Verification

1. Run a fresh non-fallback mission.
2. Watch all four handoffs become available in order.
3. Select each `REPLAY WORK PRODUCT` control and verify the 3D camera/artifact changes.
4. Select each decision-chain step and verify it targets the matching evidence stage.
5. Confirm the impact summary reports the receipt's rejected and preferred candidates and zero autonomous approvals.
6. Confirm voice, image evidence, timeline, Firestore receipt and explicit human approval still work.

Do not mark this checkpoint complete until the production-like visual check passes without console errors.
