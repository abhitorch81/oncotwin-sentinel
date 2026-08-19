import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import Settings
from .mutation_policy import is_mutation_operation, require_external_mutation


class DataHubMCP:
    """Small MCP adapter that launches the official self-hosted DataHub MCP server."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _environment(self) -> dict[str, str]:
        env = dict(os.environ)
        env.update(
            {
                "DATAHUB_GMS_URL": self.settings.datahub_gms_url,
                "DATAHUB_GMS_TOKEN": self.settings.datahub_gms_token,
                "TOOLS_IS_MUTATION_ENABLED": str(self.settings.tools_is_mutation_enabled).lower(),
            }
        )
        return env

    @asynccontextmanager
    async def session(self) -> AsyncIterator[ClientSession]:
        server = StdioServerParameters(
            command=self.settings.datahub_mcp_command,
            args=[self.settings.datahub_mcp_package],
            env=self._environment(),
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def list_tools(self) -> list[dict[str, Any]]:
        async with self.session() as session:
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in result.tools
            ]

    async def call(
        self,
        tool: str,
        arguments: dict[str, Any],
        *,
        approval_secret: str | None = None,
    ) -> dict[str, Any]:
        if is_mutation_operation(tool):
            require_external_mutation(
                self.settings,
                operation=f"datahub_mcp:{tool}",
                approval_secret=approval_secret,
            )
        started = time.perf_counter()
        async with self.session() as session:
            result = await session.call_tool(tool, arguments)
        return self._result(tool, result, started)

    async def call_many(
        self,
        calls: list[tuple[str, dict[str, Any]]],
        *,
        approval_secret: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run a grounded evidence bundle through one MCP server session.

        Reusing the process matters on Cloud Run: search, schema, lineage and
        query inspection arrive as one auditable mission without paying the
        self-hosted MCP startup cost for every tool.
        """
        for tool, _ in calls:
            if is_mutation_operation(tool):
                require_external_mutation(
                    self.settings,
                    operation=f"datahub_mcp:{tool}",
                    approval_secret=approval_secret,
                )
        results: list[dict[str, Any]] = []
        async with self.session() as session:
            for tool, arguments in calls:
                started = time.perf_counter()
                try:
                    result = await session.call_tool(tool, arguments)
                    results.append(self._result(tool, result, started))
                except Exception as exc:
                    results.append({
                        "tool": tool,
                        "is_error": True,
                        "content": [f"{type(exc).__name__}: {exc}"],
                        "duration_ms": round((time.perf_counter() - started) * 1000),
                    })
        return results

    @staticmethod
    def _result(tool: str, result: Any, started: float) -> dict[str, Any]:
        blocks: list[Any] = []
        for block in result.content:
            text = getattr(block, "text", None)
            if text is None:
                blocks.append(str(block))
                continue
            try:
                blocks.append(json.loads(text))
            except json.JSONDecodeError:
                blocks.append(text)
        return {
            "tool": tool,
            "is_error": bool(getattr(result, "isError", False)),
            "content": blocks,
            "duration_ms": round((time.perf_counter() - started) * 1000),
        }
