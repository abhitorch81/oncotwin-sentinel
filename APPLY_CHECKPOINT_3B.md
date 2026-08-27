# Apply Living Mission Theatre — Checkpoint 3B

This overlay adds receipt-grounded contextual candidate explanations. It assumes
Checkpoint 3A is already committed on `feature/living-mission-theatre`.

The selected 3D candidate, current simulation hour, deterministic receipt, policy ceiling
and Safety Steward evidence now enter one question contract. Asking why B was rejected
focuses the camera on the liver sink at the first threshold breach, changes the timeline to
T+18H, and displays the exact evidence used. The response also includes `spoken_text` for
Gemini Live, but does not claim that duplex voice is implemented yet.

```bash
cd ~/Downloads/oncotwin-agentic-multimodal
git switch feature/living-mission-theatre
unzip -o ~/Downloads/OncoTwin_Living_Mission_Theatre_Checkpoint_3B.zip -d .

source .venv-adk/bin/activate
python -m pytest -q
npm --prefix apps/web run build
git diff --check
```

Restart both servers and restore or run a successful mission. Select candidate B and click
`ASK SAFETY STEWARD WHY`, or submit `Why was candidate B rejected?` in the command capsule.

Verify:

1. No second mission is created; the existing mission receives one `/commands` request.
2. The timeline moves to T+18H and the camera focuses on the liver quarantine scene.
3. The explanation shows the 45% ceiling, first breach value, T+24H 68% accumulation,
   policy/simulation evidence IDs and receipt hash prefix.
4. The response is attributed to Safety Steward and visibly marked voice-ready.
5. Candidate C can also be selected and explained at the current timeline hour.
6. `approval_granted` remains false and the human approval boundary still works.

Do not commit until participant visual verification passes.
