from __future__ import annotations

from .condition_registry import condition
from .config import Settings


def governed_dataset_urn(settings: Settings, project: str, case_id: str) -> str:
    asset = condition(case_id)["asset_name"]
    return (
        "urn:li:dataset:(urn:li:dataPlatform:bigquery,"
        f"{project}.{settings.bigquery_dataset}.{asset},PROD)"
    )
