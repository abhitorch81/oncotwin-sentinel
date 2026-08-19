-- OncoTwin V11.1 Mutation Evolution Graph
-- Synthetic research data only. No diagnosis or treatment recommendation.

CREATE TABLE IF NOT EXISTS evolution_clones (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  clone_id UUID NOT NULL DEFAULT gen_random_uuid(),
  clone_label STRING NOT NULL,
  generation INT8 NOT NULL,
  prevalence DECIMAL(7,6) NOT NULL CHECK (prevalence >= 0 AND prevalence <= 1),
  fitness DECIMAL(7,6) NOT NULL CHECK (fitness >= 0 AND fitness <= 1),
  risk_score DECIMAL(7,6) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
  mutations JSONB NOT NULL DEFAULT '[]'::JSONB,
  first_seen TIMESTAMPTZ NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::JSONB,
  PRIMARY KEY (tenant_id, patient_id, clone_id),
  INDEX evolution_timeline_idx (tenant_id, patient_id, generation, prevalence DESC)
);

CREATE TABLE IF NOT EXISTS evolution_edges (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  parent_clone_id UUID NOT NULL,
  child_clone_id UUID NOT NULL,
  mechanism STRING NOT NULL,
  transition_probability DECIMAL(7,6) NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, parent_clone_id, child_clone_id)
);

CREATE TABLE IF NOT EXISTS mutation_events (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  mutation_event_id UUID NOT NULL DEFAULT gen_random_uuid(),
  clone_id UUID NOT NULL,
  gene STRING NOT NULL,
  alteration STRING NOT NULL,
  event_time TIMESTAMPTZ NOT NULL,
  variant_allele_fraction DECIMAL(7,6),
  evidence_strength DECIMAL(7,6) NOT NULL,
  source_name STRING,
  evidence_hash STRING NOT NULL,
  PRIMARY KEY (tenant_id, patient_id, mutation_event_id),
  UNIQUE INDEX mutation_evidence_hash_idx (tenant_id, evidence_hash),
  INDEX mutation_clone_time_idx (tenant_id, patient_id, clone_id, event_time DESC)
);

CREATE TABLE IF NOT EXISTS evolution_snapshots (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  snapshot_id UUID NOT NULL DEFAULT gen_random_uuid(),
  graph_receipt STRING NOT NULL,
  generation INT8 NOT NULL,
  dominant_clone_id UUID,
  decision STRING NOT NULL,
  projection JSONB NOT NULL,
  agent_council JSONB NOT NULL,
  human_review_required BOOL NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, snapshot_id),
  UNIQUE INDEX evolution_snapshot_receipt_idx (tenant_id, patient_id, graph_receipt)
);

CREATE TABLE IF NOT EXISTS evolution_agent_insights (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  insight_id UUID NOT NULL DEFAULT gen_random_uuid(),
  snapshot_id UUID NOT NULL,
  agent_name STRING NOT NULL,
  insight_type STRING NOT NULL,
  conclusion STRING NOT NULL,
  confidence DECIMAL(7,6) NOT NULL,
  evidence_refs JSONB NOT NULL,
  status STRING NOT NULL DEFAULT 'HUMAN_REVIEW_REQUIRED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, insight_id),
  INDEX evolution_insight_snapshot_idx (tenant_id, patient_id, snapshot_id)
);

-- A deterministic synthetic evolutionary history for ONCO-007.
INSERT INTO evolution_clones VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000001','Founder EGFR clone',0,0.720000,0.580000,0.410000,'[{"gene":"EGFR","alteration":"L858R","role":"founder"}]','2026-05-15T07:34:55Z','2026-08-15T07:34:55Z','{"assays":["DNA","scRNA"],"confidence":0.97}'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000002','TP53 subclone',1,0.440000,0.640000,0.550000,'[{"gene":"EGFR","alteration":"L858R","role":"inherited"},{"gene":"TP53","alteration":"R273H","role":"acquired"}]','2026-06-02T07:34:55Z','2026-08-15T07:34:55Z','{"assays":["DNA","ctDNA"],"confidence":0.91}'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000003','MET-amplified clone',2,0.230000,0.880000,0.940000,'[{"gene":"EGFR","alteration":"L858R","role":"inherited"},{"gene":"MET","alteration":"amplification","role":"resistance"}]','2026-07-11T07:34:55Z','2026-08-15T07:34:55Z','{"assays":["scRNA","spatial"],"confidence":0.94}'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000004','EMT-like branch',2,0.110000,0.710000,0.760000,'[{"gene":"VIM","alteration":"upregulated","role":"state-shift"},{"gene":"EPCAM","alteration":"downregulated","role":"state-shift"}]','2026-07-21T07:34:55Z','2026-08-15T07:34:55Z','{"assays":["scRNA"],"confidence":0.78}'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000005','Low-confidence bypass branch',3,0.060000,0.790000,0.820000,'[{"gene":"AXL","alteration":"high-expression","role":"hypothesis"}]','2026-08-02T07:34:55Z','2026-08-15T07:34:55Z','{"assays":["scRNA"],"confidence":0.62,"requires_validation":true}')
ON CONFLICT DO NOTHING;

INSERT INTO evolution_edges VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000001','61000000-0000-0000-0000-000000000002','acquired TP53 alteration',0.870000,'{"lineage":"DNA+ctDNA"}',now()),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000002','61000000-0000-0000-0000-000000000003','MET-selected resistant branch',0.920000,'{"lineage":"scRNA+spatial"}',now()),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000002','61000000-0000-0000-0000-000000000004','cell-state plasticity',0.740000,'{"lineage":"scRNA"}',now()),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','61000000-0000-0000-0000-000000000004','61000000-0000-0000-0000-000000000005','candidate bypass state',0.580000,'{"lineage":"inferred","requires_validation":true}',now())
ON CONFLICT DO NOTHING;

INSERT INTO mutation_events (tenant_id,patient_id,mutation_event_id,clone_id,gene,alteration,event_time,variant_allele_fraction,evidence_strength,source_name,evidence_hash) VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','62000000-0000-0000-0000-000000000001','61000000-0000-0000-0000-000000000001','EGFR','L858R','2026-05-15T07:34:55Z',0.410000,0.970000,'Synthetic DNA Pipeline','sha256:evolution-egfr-l858r'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','62000000-0000-0000-0000-000000000002','61000000-0000-0000-0000-000000000002','TP53','R273H','2026-06-02T07:34:55Z',0.260000,0.910000,'Synthetic ctDNA Pipeline','sha256:evolution-tp53-r273h'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','62000000-0000-0000-0000-000000000003','61000000-0000-0000-0000-000000000003','MET','amplification','2026-07-11T07:34:55Z',0.230000,0.940000,'Synthetic scRNA Pipeline','sha256:evolution-met-amp'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','62000000-0000-0000-0000-000000000004','61000000-0000-0000-0000-000000000005','AXL','high-expression','2026-08-02T07:34:55Z',0.060000,0.620000,'Synthetic scRNA Pipeline','sha256:evolution-axl-hypothesis')
ON CONFLICT DO NOTHING;
