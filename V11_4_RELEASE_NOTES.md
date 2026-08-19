# V11.4 release notes

## Added

- CockroachDB Operations Agent and dedicated **CRDB Ops** interface.
- Managed CockroachDB Cloud MCP client with single-cluster scope and an application-level read-tool allowlist.
- Live MCP evidence for cluster identity, table inventory, `agent_memories` schema/indexes, and running SQL activity.
- Authenticated `ccloud` inventory proof with credential-safe output.
- Runtime discovery and SHA-256 fingerprinting of the official `reviewing-cluster-health` Agent Skill.
- `cockroach_ops_runs` as persistent operational memory with tamper-evident receipts.
- Judge-facing capability, proof, and historical-run APIs.

## Preserved

- Genome Helix, Evolution Lab, persistent memory search, AWS Lambda + FastEmbed, Decision Forge, Causal Observatory, Proof Galaxy, mission workflows, and generated repairs.

## Safety

- No MCP write tools are invoked.
- Cloud MCP is scoped to one cluster.
- API keys and database credentials remain environment-only.
- Failed and partial evidence remains visible and is persisted without being upgraded into a success claim.
