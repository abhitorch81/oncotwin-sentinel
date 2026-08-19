# OncoTwin V10 Architecture

## Trust boundary

The browser never receives DataHub or Google credentials. FastAPI starts the
self-hosted DataHub MCP process over stdio. MCP performs evidence reads; GraphQL
is reserved for the separately approved condition-incident lifecycle.

```text
Three.js / browser
  -> Cloud Run FastAPI
     -> DataHub MCP (stdio) -> private GMS on Compute Engine
     -> DataHub GraphQL     -> approved incident only
     -> BigQuery            -> seven synthetic research products
     -> Vertex AI Gemini    -> grounded narration
```

## Seven condition products

Every mission resolves its canonical asset through `condition_registry.py`.
The same registry drives the mission catalog, MCP proof endpoint, 3D evidence
labels and governed write target. This prevents a visualization from silently
claiming evidence belonging to a different table.

Each proof has six measured reads: search, entity context, schema, upstream
lineage, downstream lineage and dataset queries. The normalized receipt is
hashed with SHA-256 and can be exported from Proof Galaxy.

## Execution boundary

- Evidence plane: live DataHub metadata and BigQuery catalog products.
- Simulation plane: synthetic cancer state, RL policy and 3D consequence.
- Action plane: one condition-scoped custom incident after explicit approval.
- Replay plane: cached auditable events with zero repeated mutations.

## Deployment topology

- Compute Engine `e2-standard-4`: DataHub GMS, frontend, MySQL, Kafka and
  OpenSearch.
- Cloud Run `oncotwin-mission-control`: FastAPI and static Three.js app.
- BigQuery `oncotwin`: source summaries plus seven condition products.
- Secret Manager: DataHub read/admin tokens and writeback approval secret.
- Vertex AI: Gemini narration using Cloud Run workload identity.

See `V10_RELEASE_NOTES.md` for the canonical asset map and
`scripts/18_verify_all_datahub_conditions.sh` for the judge-verification gate.
