-- Invisible mission memory: no standalone database UI.
CREATE TABLE IF NOT EXISTS mission_receipts (
  mission_id STRING PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  state STRING NOT NULL,
  prompt STRING NOT NULL,
  receipt JSONB NOT NULL,
  receipt_sha256 STRING NOT NULL UNIQUE,
  resume_cursor INT8 NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS approval_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id STRING NOT NULL REFERENCES mission_receipts(mission_id),
  actor STRING NOT NULL,
  decision STRING NOT NULL CHECK (decision IN ('approved', 'rejected')),
  channel STRING NOT NULL CHECK (channel = 'ui'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mission_receipts_created_idx ON mission_receipts (created_at DESC);

