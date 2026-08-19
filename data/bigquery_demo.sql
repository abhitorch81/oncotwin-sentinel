-- Replace PROJECT_ID before running with bq query --use_legacy_sql=false.
CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.oncotwin`
OPTIONS(location="asia-south1", description="De-identified OncoTwin hackathon analytics");

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.patient_cohorts` AS
SELECT * FROM UNNEST([
  STRUCT('P001' AS patient_key, 'Primary' AS stage, 'Responder' AS treatment_response, 54 AS age_band),
  STRUCT('P002', 'Regional', 'Stable', 61),
  STRUCT('P003', 'Metastatic', 'Non-responder', 67),
  STRUCT('P004', 'Primary', 'Responder', 48),
  STRUCT('P005', 'Metastatic', 'Stable', 59)
]);

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.cell_clusters` AS
SELECT * FROM UNNEST([
  STRUCT('C01' AS cluster_id, 'T-cell' AS cell_type, 1832 AS cell_count, 'Primary' AS dominant_stage),
  STRUCT('C02', 'Tumor epithelial', 2410, 'Regional'),
  STRUCT('C03', 'Myeloid', 1422, 'Regional'),
  STRUCT('C04', 'Metastatic tumor', 1977, 'Metastatic')
]);

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.gene_expression_summary` AS
SELECT * FROM UNNEST([
  STRUCT('P001' AS patient_key, 'C01' AS cluster_id, 'EPCAM' AS gene, 1.8 AS mean_expression, 'Primary' AS stage),
  STRUCT('P002', 'C02', 'EPCAM', 5.2, 'Regional'),
  STRUCT('P003', 'C04', 'EPCAM', 8.9, 'Metastatic'),
  STRUCT('P001', 'C01', 'MKI67', 1.1, 'Primary'),
  STRUCT('P002', 'C02', 'MKI67', 4.7, 'Regional'),
  STRUCT('P003', 'C04', 'MKI67', 9.3, 'Metastatic'),
  STRUCT('P004', 'C01', 'VIM', 2.0, 'Primary'),
  STRUCT('P005', 'C04', 'VIM', 7.8, 'Metastatic')
]);

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.progression_features` AS
SELECT
  patient_key,
  cluster_id,
  stage,
  COALESCE(AVG(IF(gene='MKI67', mean_expression, NULL)), 0.0) AS proliferation_signal,
  COALESCE(AVG(IF(gene='EPCAM', mean_expression, NULL)), 0.0) AS epithelial_signal,
  COALESCE(AVG(IF(gene='VIM', mean_expression, NULL)), 0.0) AS mesenchymal_signal,
  CURRENT_TIMESTAMP() AS generated_at
FROM `PROJECT_ID.oncotwin.gene_expression_summary`
GROUP BY patient_key, cluster_id, stage;

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.progression_scores` AS
SELECT
  patient_key,
  stage,
  cluster_id,
  LEAST(1.0, ROUND(
    0.10
    + 0.055 * proliferation_signal
    + 0.045 * epithelial_signal
    + 0.035 * mesenchymal_signal,
    2
  )) AS progression_score,
  'oncotwin-v4-lineage' AS model_version,
  CURRENT_TIMESTAMP() AS predicted_at
FROM `PROJECT_ID.oncotwin.progression_features`;

CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.quality_events` AS
SELECT * FROM UNNEST([
  STRUCT('gene_expression_summary' AS asset, 'freshness' AS check_name, 'PASS' AS status, 0.99 AS score, CURRENT_TIMESTAMP() AS checked_at),
  STRUCT('progression_features', 'completeness', 'PASS', 1.00, CURRENT_TIMESTAMP()),
  STRUCT('progression_scores', 'freshness', 'PASS', 0.98, CURRENT_TIMESTAMP()),
  STRUCT('tumour_state_transitions', 'provenance', 'PASS', 0.97, CURRENT_TIMESTAMP()),
  STRUCT('cohort_drift_metrics', 'drift_threshold', 'WARN', 0.77, CURRENT_TIMESTAMP()),
  STRUCT('genomic_schema_contract_events', 'schema_compatibility', 'PASS', 1.00, CURRENT_TIMESTAMP()),
  STRUCT('multi_omic_biomarker_evidence', 'concordance', 'WARN', 0.64, CURRENT_TIMESTAMP()),
  STRUCT('protein_conformation_states', 'structure_provenance', 'PASS', 0.93, CURRENT_TIMESTAMP()),
  STRUCT('spatial_microenvironment_states', 'spatial_context', 'WARN', 0.68, CURRENT_TIMESTAMP())
]);

-- Mission 02: a dedicated, catalogable progression-state product.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.tumour_state_transitions` AS
SELECT
  patient_key,
  cluster_id,
  stage AS from_state,
  CASE stage WHEN 'Primary' THEN 'Regional' WHEN 'Regional' THEN 'Metastatic' ELSE 'Metastatic' END AS to_state,
  ROUND(LEAST(0.99, 0.18 + progression_score * 0.72), 2) AS transition_probability,
  progression_score AS source_progression_score,
  model_version,
  CURRENT_TIMESTAMP() AS observed_at
FROM `PROJECT_ID.oncotwin.progression_scores`;

-- Mission 03: production-ML monitoring context with generating-query lineage.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.cohort_drift_metrics` AS
SELECT
  'KIRC' AS cohort_code,
  model_version,
  'progression_score' AS feature_name,
  0.42 AS baseline_mean,
  ROUND(AVG(progression_score), 2) AS serving_mean,
  ROUND(ABS(AVG(progression_score) - 0.42), 2) AS drift_score,
  IF(ABS(AVG(progression_score) - 0.42) >= 0.20, 'RETRAIN_GATE', 'MONITOR') AS decision,
  CURRENT_TIMESTAMP() AS measured_at
FROM `PROJECT_ID.oncotwin.progression_scores`
GROUP BY model_version;

-- Mission 04: governed schema-contract observations for metadata-aware codegen.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.genomic_schema_contract_events` AS
SELECT
  'schema-event-001' AS event_id,
  'gene_expression_summary' AS source_asset,
  'mean_expression' AS field_name,
  'FLOAT64' AS expected_type,
  'FLOAT64' AS observed_type,
  'COMPATIBLE' AS compatibility,
  'progression_features' AS downstream_asset,
  CURRENT_TIMESTAMP() AS detected_at
FROM (SELECT 1 FROM `PROJECT_ID.oncotwin.gene_expression_summary` LIMIT 1);

-- Mission 05: multi-omic concordance with explicit RNA/variant/protein evidence.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.multi_omic_biomarker_evidence` AS
SELECT
  patient_key,
  gene,
  ROUND(AVG(mean_expression), 2) AS rna_signal,
  IF(gene IN ('MKI67', 'VIM'), 'DETECTED', 'REFERENCE') AS variant_call,
  ROUND(AVG(mean_expression) * IF(gene = 'EPCAM', 0.92, 0.74), 2) AS protein_signal,
  ROUND(GREATEST(0.0, 1.0 - ABS(AVG(mean_expression) - AVG(mean_expression) * IF(gene = 'EPCAM', 0.92, 0.74)) / 10.0), 2) AS concordance_score,
  IF(gene = 'VIM', 'REVIEW', 'CONCORDANT') AS evidence_state,
  CURRENT_TIMESTAMP() AS evaluated_at
FROM `PROJECT_ID.oncotwin.gene_expression_summary`
GROUP BY patient_key, gene;

-- Mission 06: schematic structure evidence; this is provenance, not folding prediction.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.protein_conformation_states` AS
SELECT
  CONCAT(gene, '-canonical') AS protein_id,
  gene,
  'seq-v1' AS sequence_version,
  'research-structure-demo-v1' AS structure_model,
  IF(evidence_state = 'CONCORDANT', 'native-like', 'provenance-rift') AS conformation_state,
  concordance_score AS confidence_score,
  IF(evidence_state = 'CONCORDANT', 'VERIFIED', 'REVIEW_REQUIRED') AS provenance_status,
  CURRENT_TIMESTAMP() AS scored_at
FROM `PROJECT_ID.oncotwin.multi_omic_biomarker_evidence`;

-- Mission 07: spatial immune-context product derived from governed cell clusters.
CREATE OR REPLACE TABLE `PROJECT_ID.oncotwin.spatial_microenvironment_states` AS
SELECT
  CONCAT('R', LPAD(CAST(ROW_NUMBER() OVER(ORDER BY cluster_id) AS STRING), 2, '0')) AS region_id,
  cluster_id,
  cell_type,
  ROUND(12.0 + ROW_NUMBER() OVER(ORDER BY cluster_id) * 8.5, 1) AS immune_distance,
  ROUND(IF(cell_type = 'Metastatic tumor', 0.62, 0.18), 2) AS malignant_fraction,
  IF(cell_type = 'Metastatic tumor', 'immune-excluded', 'inflamed') AS spatial_state,
  cell_type = 'Metastatic tumor' AS review_required,
  CURRENT_TIMESTAMP() AS measured_at
FROM `PROJECT_ID.oncotwin.cell_clusters`;
