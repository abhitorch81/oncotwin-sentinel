# OncoTwin V11.2 Release Notes

## Persistent memory becomes a learning loop

V11.2 upgrades the Evolution Lab from a single forward simulation into a persistent time machine. CockroachDB now remembers what the graph looked like, what agents expected next, how they voted, and where later evidence disagreed.

### New judge-visible moments

1. **Restart-proof replay** — click through four observation frames and watch the 3D clone population reconstruct itself.
2. **Memory-conditioned branching** — vary selection pressure and generate four competing futures rather than one answer.
3. **Tandem-agent disagreement** — five specialist roles cast explicit, inspectable path votes.
4. **Forecast reconciliation** — an earlier forecast is compared with the latest observation; unexpected EMT and AXL expansion remains visible.
5. **Auditable persistence** — frames, paths, votes, evidence references and reconciliation records are stored in CockroachDB with deterministic receipts.

### Technology proof

- CockroachDB: 14 domain tables plus a distributed vector index.
- AWS Lambda: serverless FastEmbed inference for semantic memory retrieval.
- Open-source embeddings: `BAAI/bge-small-en-v1.5`.
- Three.js: interactive clone graph, historical replay and projected branch overlays.
- Five-agent evolution council with a mandatory human-review boundary.

### Safety boundary

All records are synthetic. Evolution paths are research hypotheses and cannot trigger a clinical action.
