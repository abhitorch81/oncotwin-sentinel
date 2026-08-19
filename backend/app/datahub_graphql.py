from __future__ import annotations

import json
from typing import Any

import httpx

from .config import Settings


class DataHubGraphQL:
    """Small governed surface for DataHub operations not exposed by our MCP server."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.url = settings.datahub_gms_url.rstrip("/") + "/api/graphql"

    async def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
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

    async def resolve_incident(self, incident_urn: str, message: str) -> bool:
        data = await self.execute(
            """
            mutation ResolveIncident($urn: String!, $message: String!) {
              updateIncidentStatus(urn: $urn, input: {state: RESOLVED, message: $message})
            }
            """,
            {"urn": incident_urn, "message": message},
        )
        return bool(data.get("updateIncidentStatus"))

    async def raise_incident(
        self,
        asset_urn: str,
        title: str,
        description: str,
        custom_type: str = "ONCOTWIN_CANCER_CONTEXT",
    ) -> str | None:
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
