# OncoTwin V11.4 — CockroachDB Operations Agent

This overlay adds a judge-verifiable integration of all four CockroachDB AI surfaces used by OncoTwin:

1. Managed CockroachDB Cloud MCP Server for live, typed cluster reads.
2. `ccloud` for authenticated Cloud cluster inventory.
3. The official `reviewing-cluster-health` Agent Skill from `cockroachlabs/cockroachdb-skills`.
4. Existing Distributed Vector Indexing for semantic clinical memory.

The Operations Agent makes only read MCP calls. It persists its own audit receipt through the application database connection into `cockroach_ops_runs`. Every proof records tool names, latency, success/failure, the official skill hash, ccloud verification, the exact set of server-registered tools, and a SHA-256 receipt.

## 1. Apply the overlay

Copy the contents of this package over the OncoTwin project root, preserving existing files.

## 2. Install `ccloud` and official Agent Skills

From the project root on the Mac:

```bash
bash scripts/setup_cockroach_tooling_macos.sh
ccloud auth login
bash scripts/install_cockroach_agent_skills.sh
```

When the skills installer asks what to install, include `reviewing-cluster-health` and install it for this project.

## 3. Create a CockroachDB Cloud MCP service account

In CockroachDB Cloud:

1. Create a service account for the demo.
2. Assign only the minimum cluster role required for read inspection.
3. Create an API key and copy the secret once.
4. Use the existing cluster ID from the browser URL: the value after `/cluster/` and before the next `/`.

The app scopes every MCP request to that one cluster using the `mcp-cluster-id` header. Never commit the API key.

## 4. Configure the current terminal securely

```bash
export COCKROACH_MCP_ENABLED=true
export COCKROACH_MCP_TRANSPORT=cloud_http
export COCKROACH_MCP_URL=https://cockroachlabs.cloud/mcp
read -s "COCKROACH_MCP_API_KEY?Paste the service-account API key: "
echo
export COCKROACH_MCP_API_KEY
read "COCKROACH_MCP_CLUSTER_ID?Paste the cluster ID: "
export COCKROACH_MCP_CLUSTER_ID
```

Recover `DATABASE_URL` from AWS Secrets Manager exactly as before. Do not paste it into source files.

## 5. Apply the receipt schema

```bash
python3 scripts/apply_cockroach_ops_schema.py
```

## 6. Start OncoTwin

Run from the project root in the same terminal containing the exported values:

```bash
source .venv-crdb/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the app, select **CRDB Ops**, and click **Run live CockroachDB proof**.

## Verification commands

```bash
curl -sS http://127.0.0.1:8000/api/cockroach/ops/capabilities | python3 -m json.tool
curl -sS -X POST http://127.0.0.1:8000/api/cockroach/ops/proof | python3 -m json.tool
curl -sS http://127.0.0.1:8000/api/cockroach/ops/runs | python3 -m json.tool
```

Do not claim a tool is integrated until the capabilities endpoint reports it connected/installed and the proof endpoint returns live evidence. A `PARTIAL` receipt is retained honestly; it is not presented as a pass.

## Judge explanation

- **MCP Server:** The Operations Agent calls `get_cluster`, `list_tables`, `get_table_schema`, `show_running_queries`, and `show_statement` against the live, cluster-scoped managed MCP endpoint. It never invokes a write tool.
- **ccloud CLI:** The agent runs `ccloud cluster list`, extracts only cluster name/ID evidence, hashes the complete output, and proves that the Cloud control plane is authenticated without exposing credentials.
- **Agent Skills:** The official `reviewing-cluster-health` skill defines the diagnostic workflow. The installed `SKILL.md` is SHA-256 fingerprinted into each proof receipt so the workflow is attributable and reproducible.
- **Distributed Vector Index:** The existing `agent_memories_embedding_idx` supports semantic retrieval of durable agent memory, filtered by tenant and patient.
- **CockroachDB memory:** Tool outcomes and receipts are stored in `cockroach_ops_runs`, allowing the agent to compare operational state across restarts and later runs.
