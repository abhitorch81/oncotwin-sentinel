from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .config import Settings
from .mutation_policy import require_external_mutation


class DataHubGraphQL:
    """Small governed surface for DataHub operations not exposed by our MCP server."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.url = settings.datahub_gms_url.rstrip("/") + "/api/graphql"

    async def execute(
        self,
        query: str,
        variables: dict[str, Any],
        *,
        approval_secret: str | None = None,
    ) -> dict[str, Any]:
        if re.search(r"\bmutation\b", query, flags=re.IGNORECASE):
            require_external_mutation(
                self.settings,
                operation="datahub_graphql_mutation",
                approval_secret=approval_secret,
            )
        headers = {"Content-Type": "application/json"}
        if self.settings.datahub_admin_token:
            headers["Authorization"] = f"Bearer {self.settings.datahub_admin_token}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.url, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise RuntimeError(body["errors"][0].get("message", "DataHub GraphQL error"))
        return body.get("data", {})

    async def resolve_incident(
        self,
        incident_urn: str,
        message: str,
        *,
        approval_secret: str | None,
    ) -> bool:
        require_external_mutation(
            self.settings,
            operation="datahub_resolve_incident",
            approval_secret=approval_secret,
        )
        data = await self.execute(
            """
            mutation ResolveIncident($urn: String!, $message: String!) {
              updateIncidentStatus(urn: $urn, input: {state: RESOLVED, message: $message})
            }
            """,
            {"urn": incident_urn, "message": message},
            approval_secret=approval_secret,
        )
        return bool(data.get("updateIncidentStatus"))

    async def raise_incident(
        self,
        asset_urn: str,
        title: str,
        description: str,
        custom_type: str = "ONCOTWIN_CANCER_CONTEXT",
        *,
        approval_secret: str | None,
    ) -> str | None:
        require_external_mutation(
            self.settings,
            operation="datahub_raise_incident",
            approval_secret=approval_secret,
        )
        # These values are server-controlled, but JSON encoding also produces
        # valid GraphQL string literals and prevents accidental quote injection.
        data = await self.execute(
            f"""
            mutation {{
              raiseIncident(input: {{
                resourceUrn: {json.dumps(asset_urn)}
                type: CUSTOM
                customType: {json.dumps(custom_type)}
                title: {json.dumps(title)}
                description: {json.dumps(description)}
                priority: HIGH
              }})
            }}
            """,
            {},
            approval_secret=approval_secret,
        )
        value = data.get("raiseIncident")
        return str(value) if value else None

    async def active_incidents(self, asset_urn: str) -> dict[str, Any]:
        return await self.execute(
            """
            query ActiveIncidents($urn: String!) {
              dataset(urn: $urn) {
                incidents(state: ACTIVE, start: 0, count: 20) {
                  total
                  incidents { urn incidentType title status { state } }
                }
              }
            }
            """,
            {"urn": asset_urn},
        )
