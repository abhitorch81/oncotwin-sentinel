-- OncoTwin V11.2 Persistent Evolution Memory
-- Synthetic research data only. No diagnosis or treatment recommendation.

CREATE TABLE IF NOT EXISTS evolution_memory_frames (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  frame_id UUID NOT NULL DEFAULT gen_random_uuid(),
  generation INT8 NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  clone_distribution JSONB NOT NULL,
  evidence_refs JSONB NOT NULL DEFAULT '[]'::JSONB,
  frame_receipt STRING NOT NULL,
  source_name STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, frame_id),
  UNIQUE INDEX evolution_memory_frame_receipt_idx (tenant_id, patient_id, frame_receipt),
  INDEX evolution_memory_frame_time_idx (tenant_id, patient_id, generation, observed_at DESC)
);

CREATE TABLE IF NOT EXISTS evolution_path_hypotheses (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  path_id UUID NOT NULL DEFAULT gen_random_uuid(),
  base_frame_id UUID NOT NULL,
  scenario STRING NOT NULL,
  pressure_mode STRING NOT NULL,
  horizon INT8 NOT NULL,
  probability DECIMAL(7,6) NOT NULL,
  trajectories JSONB NOT NULL,
  agent_votes JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  path_receipt STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, path_id),
  UNIQUE INDEX evolution_path_receipt_idx (tenant_id, patient_id, path_receipt),
  INDEX evolution_path_time_idx (tenant_id, patient_id, created_at DESC)
);

CREATE TABLE IF NOT EXISTS evolution_memory_reconciliations (
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  reconciliation_id UUID NOT NULL DEFAULT gen_random_uuid(),
  path_id UUID NOT NULL,
  observed_frame_id UUID NOT NULL,
  divergence_score DECIMAL(7,6) NOT NULL,
  surprises JSONB NOT NULL,
  status STRING NOT NULL,
  receipt STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, patient_id, reconciliation_id),
  UNIQUE INDEX evolution_reconciliation_receipt_idx (tenant_id, patient_id, receipt)
);

INSERT INTO evolution_memory_frames (tenant_id,patient_id,frame_id,generation,observed_at,clone_distribution,evidence_refs,frame_receipt,source_name) VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','71000000-0000-0000-0000-000000000001',0,'2026-05-15T07:34:55Z','{"61000000-0000-0000-0000-000000000001":1.0}','["sha256:evolution-egfr-l858r"]','faec6aef9d9159e38d0fbc1d16b93a03072bfcffcef76a17c7816a08b13a2846','Synthetic baseline assay'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','71000000-0000-0000-0000-000000000002',1,'2026-06-02T07:34:55Z','{"61000000-0000-0000-0000-000000000001":0.72,"61000000-0000-0000-0000-000000000002":0.28}','["sha256:evolution-egfr-l858r","sha256:evolution-tp53-r273h"]','b1e418264011e9d459dcaae870bda97287098c9c7f622f444d01fc978adc7677','Synthetic DNA + ctDNA assay'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','71000000-0000-0000-0000-000000000003',2,'2026-07-11T07:34:55Z','{"61000000-0000-0000-0000-000000000001":0.52,"61000000-0000-0000-0000-000000000002":0.35,"61000000-0000-0000-0000-000000000003":0.09,"61000000-0000-0000-0000-000000000004":0.04}','["sha256:evolution-met-amp"]','af507b0de2bc49fed4d396e934eef0e213599bb67dabba8036dab01f1d5c9fc4','Synthetic single-cell + spatial assay'),
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','71000000-0000-0000-0000-000000000004',3,'2026-08-15T07:34:55Z','{"61000000-0000-0000-0000-000000000001":0.38,"61000000-0000-0000-0000-000000000002":0.25,"61000000-0000-0000-0000-000000000003":0.19,"61000000-0000-0000-0000-000000000004":0.12,"61000000-0000-0000-0000-000000000005":0.06}','["sha256:evolution-met-amp","sha256:evolution-axl-hypothesis"]','e14d569107c908370abf811828829954b0a88b5e37ac762988f3d1530d7badbc','Synthetic longitudinal fusion')
ON CONFLICT DO NOTHING;

-- A remembered forecast and its later observation demonstrate reconciliation.
INSERT INTO evolution_path_hypotheses (tenant_id,patient_id,path_id,base_frame_id,scenario,pressure_mode,horizon,probability,trajectories,agent_votes,memory_refs,path_receipt,created_at) VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','72000000-0000-0000-0000-000000000001','71000000-0000-0000-0000-000000000003','resistance_sweep','balanced',1,0.410000,'[{"clone_id":"61000000-0000-0000-0000-000000000001","clone_label":"Founder EGFR clone","trajectory":[{"generation":3,"prevalence":0.43,"uncertainty":0.09}]},{"clone_id":"61000000-0000-0000-0000-000000000002","clone_label":"TP53 subclone","trajectory":[{"generation":3,"prevalence":0.28,"uncertainty":0.09}]},{"clone_id":"61000000-0000-0000-0000-000000000003","clone_label":"MET-amplified clone","trajectory":[{"generation":3,"prevalence":0.20,"uncertainty":0.11}]},{"clone_id":"61000000-0000-0000-0000-000000000004","clone_label":"EMT-like branch","trajectory":[{"generation":3,"prevalence":0.07,"uncertainty":0.14}]},{"clone_id":"61000000-0000-0000-0000-000000000005","clone_label":"Low-confidence bypass branch","trajectory":[{"generation":3,"prevalence":0.02,"uncertainty":0.18}]}]','[{"agent":"Clonal Evolution Forecaster","supports":true},{"agent":"Evidence Challenger","supports":false},{"agent":"Memory Sentinel","supports":true}]','{"base_frame_receipt":"af507b0de2bc49fed4d396e934eef0e213599bb67dabba8036dab01f1d5c9fc4","memory_ids":["30000000-0000-0000-0000-000000000001"]}','487c345dba7f7fd5a00398f91697b9bf1176da564f389b630063d11fc1f1efa9','2026-07-11T08:00:00Z')
ON CONFLICT DO NOTHING;

INSERT INTO evolution_memory_reconciliations (tenant_id,patient_id,reconciliation_id,path_id,observed_frame_id,divergence_score,surprises,status,receipt,created_at) VALUES
('11111111-1111-1111-1111-111111111111','00700700-0000-0000-0000-000000000007','73000000-0000-0000-0000-000000000001','72000000-0000-0000-0000-000000000001','71000000-0000-0000-0000-000000000004',0.070000,'[{"clone_label":"EMT-like branch","delta":0.05},{"clone_label":"Low-confidence bypass branch","delta":0.04},{"clone_label":"Founder EGFR clone","delta":-0.05}]','OBSERVATION_DIVERGED','a34f8e93b85584eb23c672135b2ba1a09ab168aa6afdb38b19937a7f0ef860a1','2026-08-15T08:00:00Z')
ON CONFLICT DO NOTHING;
