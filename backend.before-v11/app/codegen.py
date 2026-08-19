import hashlib
import json
import re
from typing import Any


class MetadataAwareRepairEngineer:
    """Build reviewable data-code artifacts only after DataHub context is available."""

    def _field_names(self, value: Any) -> list[str]:
        names: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, child in node.items():
                    if key.lower() in {"field", "fieldpath", "field_path", "name"} and isinstance(child, str):
                        candidate = child.rsplit(".", 1)[-1].strip()
                        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
                            names.append(candidate)
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)
        return list(dict.fromkeys(names))

    def generate(self, urn: str, schema: Any, lineage: Any) -> dict[str, Any]:
        fields = self._field_names(schema)
        preferred = [
            name
            for name in ("patient_key", "cluster_id", "stage", "progression_score", "predicted_at")
            if name in fields
        ]
        guarded_fields = preferred or fields[:5] or ["progression_score"]
        context = json.dumps({"urn": urn, "schema": schema, "lineage": lineage}, sort_keys=True, default=str)
        fingerprint = hashlib.sha256(context.encode()).hexdigest()[:16]
        tests = "\n".join(f"      - name: {name}\n        tests: [not_null]" for name in guarded_fields[:4])

        dbt = f'''# Generated only after DataHub schema + lineage inspection
# source_urn: {urn}
# context_fingerprint: {fingerprint}
version: 2
models:
  - name: progression_scores
    description: "Governed cancer-progression features protected by DataHub context"
    columns:
{tests}
    meta:
      datahub_urn: "{urn}"
      context_fingerprint: "{fingerprint}"
'''
        airflow = f'''# DataHub Skills workflow artifact: quality -> lineage -> guarded action
from airflow.exceptions import AirflowFailException

DATAHUB_URN = "{urn}"
CONTEXT_FINGERPRINT = "{fingerprint}"

def guard_progression_features(completeness: float) -> dict:
    if completeness < 0.82:
        raise AirflowFailException(
            f"Blocked downstream cancer model: completeness={{completeness:.2%}}"
        )
    return {{"status": "safe", "datahub_urn": DATAHUB_URN}}
'''
        ingestion = f'''# DataHub ingestion patch generated from inspected catalog context
source:
  type: bigquery
  config:
    project_id: "${{GCP_PROJECT_ID}}"
    include_table_lineage: true
    include_column_lineage: true
    include_usage_statistics: true
    profiling:
      enabled: true
sink:
  type: datahub-rest
  config:
    server: "${{DATAHUB_GMS_URL}}"
    token: "${{DATAHUB_GMS_TOKEN}}"
# context_fingerprint: {fingerprint}
'''
        return {
            "context_fingerprint": fingerprint,
            "source_urn": urn,
            "schema_fields_used": guarded_fields,
            "skills": ["datahub-search", "datahub-quality", "datahub-lineage"],
            "artifacts": {"dbt": dbt, "airflow": airflow, "python": ingestion},
        }
