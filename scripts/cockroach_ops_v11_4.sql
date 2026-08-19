CREATE TABLE IF NOT EXISTS cockroach_ops_runs (
  run_id UUID PRIMARY KEY,
  captured_at TIMESTAMPTZ NOT NULL,
  skill_name STRING NOT NULL,
  skill_sha256 STRING,
  mcp_transport STRING NOT NULL,
  mcp_tools JSONB NOT NULL,
  ccloud_verified BOOL NOT NULL,
  read_only_verified BOOL NOT NULL,
  status STRING NOT NULL CHECK (status IN ('PASS', 'PARTIAL', 'FAIL')),
  evidence JSONB NOT NULL,
  receipt_sha256 STRING NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cockroach_ops_runs_captured_idx
ON cockroach_ops_runs (captured_at DESC)
STORING (status, ccloud_verified, read_only_verified, receipt_sha256);

GRANT SELECT, INSERT ON TABLE cockroach_ops_runs TO oncotwin_app;
