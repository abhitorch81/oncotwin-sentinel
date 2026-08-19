"""Read-only CockroachDB operations agent with MCP, ccloud, and Agent Skills proof."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shlex
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from sqlalchemy import text

from .config import get_settings
from .database import get_engine

READ_ONLY_TOOLS = {
    "list_clusters",
    "list_databases",
    "list_tables",
    "get_table_schema",
    "get_cluster",
    "list_sql_users",
    "list_cluster_nodes",
    "show_running_queries",
    "select_query",
    "explain_query",
    "show_statement",
}
PROOF_CALLS = [
    ("get_cluster", {}),
    ("list_tables", {"database": "oncotwin", "limit": 100}),
    ("get_table_schema", {"database": "oncotwin", "schema": "public", "table": "agent_memories"}),
    ("show_running_queries", {"limit": 20}),
    ("show_statement", {"query": "SHOW INDEXES FROM oncotwin.public.agent_memories", "limit": 100}),
]


def _jsonable_content(result: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in getattr(result, "content", []) or []:
        if hasattr(item, "model_dump"):
            output.append(item.model_dump(mode="json"))
        elif isinstance(item, dict):
            output.append(item)
        else:
            output.append({"type": "text", "text": str(item)})
    return output


def _mcp_environment() -> dict[str, str]:
    settings = get_settings()
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    if url.startswith("cockroachdb://"):
        url = "postgresql://" + url[len("cockroachdb://"):]
    env = os.environ.copy()
    env.update({
        "CRDB_DATABASE_URL": url,
        "CRDB_MCP_ENABLE_WRITE_QUERIES": "false",
        "CRDB_MCP_QUERY_TIMEOUT": f"{max(1, int(settings.cockroach_mcp_timeout_seconds))}s",
        "CRDB_MCP_MAX_ROWS_COUNT": "250",
        "CRDB_MCP_MAX_CONNS": "3",
        "CRDB_MCP_TXN_QOS": "background",
        "CRDB_MCP_LOG_LEVEL": "error",
    })
    # Current Cloud URL uses a password. This is an explicit compatibility opt-in;
    # the MCP role's SQL grants remain the hard permission boundary.
    if urlsplit(url).password:
        env["CRDB_MCP_ALLOW_PASSWORD_AUTH"] = "true"
    return env


def _skill_candidates() -> list[Path]:
    configured = Path(get_settings().cockroach_skill_path).expanduser()
    roots = [configured]
    if not configured.is_absolute():
        roots.extend([
            Path.cwd() / configured,
            Path.cwd() / ".agents/skills/cockroachdb-operations-and-lifecycle/reviewing-cluster-health/SKILL.md",
        ])
    for base in (Path.cwd() / ".agents/skills", Path.cwd() / ".claude/skills", Path.cwd() / ".cursor/skills"):
        roots.extend(base.glob("**/reviewing-cluster-health/SKILL.md"))
    return roots


@asynccontextmanager
async def _transport():
    settings = get_settings()
    if settings.cockroach_mcp_transport == "cloud_http":
        if not settings.cockroach_mcp_api_key or not settings.cockroach_mcp_cluster_id:
            raise RuntimeError("COCKROACH_MCP_API_KEY and COCKROACH_MCP_CLUSTER_ID are required for the managed Cloud MCP server")
        headers = {
            "Authorization": f"Bearer {settings.cockroach_mcp_api_key}",
            "mcp-cluster-id": settings.cockroach_mcp_cluster_id,
        }
        async with streamablehttp_client(settings.cockroach_mcp_url, headers=headers) as streams:
            yield streams[0], streams[1]
        return
    args = json.loads(settings.cockroach_mcp_args_json or "[]")
    command = shlex.split(settings.cockroach_mcp_command)[0]
    params = StdioServerParameters(command=command, args=args, env=_mcp_environment())
    async with stdio_client(params) as (reader, writer):
        yield reader, writer


def skill_evidence() -> dict[str, Any]:
    for path in _skill_candidates():
        if path.is_file():
            raw = path.read_bytes()
            markdown = raw.decode(errors="replace")
            sections = [match.group(1).strip() for match in re.finditer(r"^##+\s+(.+)$", markdown, re.MULTILINE)]
            return {
                "installed": True,
                "name": "reviewing-cluster-health",
                "source": "cockroachlabs/cockroachdb-skills",
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "sections_loaded": sections[:20],
                "workflow": ["gather deployment context", "inspect live cluster", "review SQL activity", "assess production posture"],
                "safety": "read-only diagnostic branch; no cancellation, settings, grant, or DDL action",
            }
    return {
        "installed": False,
        "name": "reviewing-cluster-health",
        "source": "cockroachlabs/cockroachdb-skills",
        "install_command": "npx skills add cockroachlabs/cockroachdb-skills",
        "safety": "proof is blocked until the official SKILL.md is present",
    }


async def mcp_capabilities() -> dict[str, Any]:
    settings = get_settings()
    if not settings.cockroach_mcp_enabled:
        return {"enabled": False, "connected": False, "reason": "COCKROACH_MCP_ENABLED is false"}
    if settings.cockroach_mcp_transport != "cloud_http":
        command = shlex.split(settings.cockroach_mcp_command)[0]
        if not shutil.which(command) and not Path(command).exists():
            return {"enabled": True, "connected": False, "reason": f"MCP command not found: {command}"}
    try:
        async with _transport() as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await asyncio.wait_for(session.initialize(), timeout=settings.cockroach_mcp_timeout_seconds)
                listed = await asyncio.wait_for(session.list_tools(), timeout=settings.cockroach_mcp_timeout_seconds)
        tools = sorted(tool.name for tool in listed.tools)
        writes = sorted(set(tools) - READ_ONLY_TOOLS)
        return {"enabled": True, "connected": True, "transport": settings.cockroach_mcp_transport, "tools": tools, "write_tools_exposed": writes, "read_only_policy": "application allowlist invokes only official read tools"}
    except Exception as error:
        return {"enabled": True, "connected": False, "reason": str(error), "error_type": type(error).__name__}


async def _run_mcp_calls() -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    evidence: list[dict[str, Any]] = []
    async with _transport() as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await asyncio.wait_for(session.initialize(), timeout=settings.cockroach_mcp_timeout_seconds)
            listed = await asyncio.wait_for(session.list_tools(), timeout=settings.cockroach_mcp_timeout_seconds)
            registered = {tool.name for tool in listed.tools}
            for name, arguments in PROOF_CALLS:
                if name not in READ_ONLY_TOOLS:
                    raise RuntimeError(f"MCP policy rejected non-read tool: {name}")
                started = time.perf_counter()
                try:
                    result = await asyncio.wait_for(session.call_tool(name, arguments), timeout=settings.cockroach_mcp_timeout_seconds)
                    content = _jsonable_content(result)
                    evidence.append({"tool": name, "ok": not bool(getattr(result, "isError", False)), "duration_ms": round((time.perf_counter() - started) * 1000, 2), "content": content})
                except Exception as error:
                    evidence.append({"tool": name, "ok": False, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "error_type": type(error).__name__, "message": str(error)})
    return evidence, sorted(registered)


async def ccloud_evidence() -> dict[str, Any]:
    settings = get_settings()
    binary = shutil.which(settings.ccloud_command)
    if not binary:
        return {"installed": False, "authenticated": False, "reason": "ccloud command not found"}
    try:
        version = await asyncio.create_subprocess_exec(binary, "version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        version_out, _ = await asyncio.wait_for(version.communicate(), timeout=settings.ccloud_timeout_seconds)
        proc = await asyncio.create_subprocess_exec(binary, "cluster", "list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=settings.ccloud_timeout_seconds)
        if proc.returncode != 0:
            return {"installed": True, "authenticated": False, "version": version_out.decode(errors="replace").strip(), "reason": stderr.decode(errors="replace").strip()[:400]}
        output = stdout.decode(errors="replace")
        cluster_pattern = re.compile(r"^\s*(\S+)\s+([0-9a-fA-F-]{36})\s+(\S+)", re.MULTILINE)
        safe = [{"name": match.group(1), "id": match.group(2), "plan": match.group(3)} for match in cluster_pattern.finditer(output)]
        scoped_id = settings.cockroach_mcp_cluster_id
        return {"installed": True, "authenticated": True, "version": version_out.decode(errors="replace").strip(), "command": "ccloud cluster list", "clusters": safe, "cluster_count": len(safe), "scoped_cluster_visible": any(item["id"] == scoped_id for item in safe) if scoped_id else None, "output_sha256": hashlib.sha256(output.encode()).hexdigest(), "credentials_exposed": False}
    except Exception as error:
        return {"installed": True, "authenticated": False, "error_type": type(error).__name__, "reason": str(error)}


def _persist_receipt(payload: dict[str, Any]) -> None:
    with get_engine().begin() as connection:
        connection.execute(text("""
            INSERT INTO cockroach_ops_runs
              (run_id, captured_at, skill_name, skill_sha256, mcp_transport, mcp_tools,
               ccloud_verified, read_only_verified, status, evidence, receipt_sha256)
            VALUES
              (CAST(:run_id AS UUID), :captured_at, :skill_name, :skill_sha256, :mcp_transport,
               CAST(:mcp_tools AS JSONB), :ccloud_verified, :read_only_verified, :status,
               CAST(:evidence AS JSONB), :receipt_sha256)
            ON CONFLICT (run_id) DO NOTHING
        """), {
            "run_id": payload["run_id"], "captured_at": payload["captured_at"],
            "skill_name": payload["agent_skill"]["name"], "skill_sha256": payload["agent_skill"].get("sha256"), "mcp_transport": payload["mcp_transport"],
            "mcp_tools": json.dumps(payload["registered_mcp_tools"]), "ccloud_verified": payload["ccloud"].get("authenticated", False),
            "read_only_verified": payload["read_only_verified"], "status": payload["status"],
            "evidence": json.dumps({"skill_application": payload["skill_application"], "mcp": payload["mcp_evidence"], "ccloud": payload["ccloud"]}, default=str),
            "receipt_sha256": payload["receipt_sha256"],
        })


async def run_operations_proof() -> dict[str, Any]:
    settings = get_settings()
    if not settings.cockroach_mcp_enabled:
        raise RuntimeError("CockroachDB MCP is disabled. Set COCKROACH_MCP_ENABLED=true.")
    skill = skill_evidence()
    if not skill["installed"]:
        raise RuntimeError("Official CockroachDB Agent Skill is not installed. Run scripts/install_cockroach_agent_skills.sh.")
    ccloud = await ccloud_evidence()
    skill_application = {
        "inputs": {"deployment_tier": "CockroachDB Cloud", "reason": "hackathon production-readiness proof", "access": "managed MCP + ccloud"},
        "selected_branch": "Cloud health review",
        "executed_checks": ["cluster identity", "table inventory", "critical memory schema and index", "live SQL activity", "Cloud control-plane inventory"],
        "skipped_mutations": ["cancel query", "change setting", "modify grant", "DDL"],
        "source_sha256": skill["sha256"],
    }
    mcp_evidence, registered = await _run_mcp_calls()
    write_tools_exposed = sorted(set(registered) - READ_ONLY_TOOLS)
    read_only = all(name in READ_ONLY_TOOLS for name, _ in PROOF_CALLS)
    captured_at = datetime.now(timezone.utc).isoformat()
    run_id = str(uuid.uuid4())
    status = "PASS" if all(item["ok"] for item in mcp_evidence) and ccloud.get("authenticated") and read_only else "PARTIAL"
    receipt_input = {"run_id": run_id, "captured_at": captured_at, "skill": skill_application, "registered": registered, "mcp": mcp_evidence, "ccloud": ccloud, "read_only": read_only}
    receipt = hashlib.sha256(json.dumps(receipt_input, sort_keys=True, default=str).encode()).hexdigest()
    payload = {"ok": status == "PASS", "status": status, "run_id": run_id, "captured_at": captured_at, "agent": "CockroachDB Operations Agent", "mcp_transport": settings.cockroach_mcp_transport, "agent_skill": skill, "skill_application": skill_application, "registered_mcp_tools": registered, "mcp_evidence": mcp_evidence, "ccloud": ccloud, "read_only_verified": read_only, "write_tools_exposed": write_tools_exposed, "write_tools_invoked": [], "cockroachdb_persisted": True, "receipt_sha256": receipt}
    _persist_receipt(payload)
    return payload


def recent_runs(limit: int = 10) -> list[dict[str, Any]]:
    with get_engine().connect() as connection:
        rows = connection.execute(text("SELECT run_id, captured_at, skill_name, skill_sha256, mcp_transport, mcp_tools, ccloud_verified, read_only_verified, status, receipt_sha256 FROM cockroach_ops_runs ORDER BY captured_at DESC LIMIT :limit"), {"limit": min(max(limit, 1), 50)}).mappings().all()
    return [dict(row) for row in rows]
