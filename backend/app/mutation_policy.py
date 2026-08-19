from __future__ import annotations

import secrets
from typing import Any

from .config import Settings


DEFAULT_APPROVAL_SECRETS = {"", "change-me", "changeme"}
MUTATION_PREFIXES = (
    "add_",
    "create_",
    "delete_",
    "emit_",
    "execute_",
    "modify_",
    "patch_",
    "publish_",
    "raise_",
    "remove_",
    "replace_",
    "resolve_",
    "save_",
    "set_",
    "update_",
    "upsert_",
    "write_",
)


class MutationPolicyError(PermissionError):
    """Raised when an external write fails the fail-closed policy."""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"External mutation blocked for {operation}: {reason}")


def is_mutation_operation(operation: str) -> bool:
    normalized = operation.strip().lower().replace("-", "_")
    return normalized.startswith(MUTATION_PREFIXES)


def approval_secret_is_configured(settings: Settings) -> bool:
    value = settings.writeback_approval_secret.strip()
    return value.lower() not in DEFAULT_APPROVAL_SECRETS and len(value) >= 16


def approval_secret_matches(settings: Settings, supplied: str | None) -> bool:
    return secrets.compare_digest(supplied or "", settings.writeback_approval_secret)


def require_external_mutation(
    settings: Settings,
    *,
    operation: str,
    approval_secret: str | None,
) -> None:
    """Authorize one external write or fail closed.

    Demo mode is simulation-only. Live writes require the global mutation flag,
    mandatory human approval, a non-default configured secret, and a matching
    request secret. Low-level clients call this again even when an API route has
    already authorized the request.
    """

    if settings.demo_mode:
        raise MutationPolicyError(operation, "demo mode never performs external writes")
    if not settings.tools_is_mutation_enabled:
        raise MutationPolicyError(operation, "external mutations are disabled")
    if not settings.human_approval_required:
        raise MutationPolicyError(operation, "human approval policy is not enabled")
    if not approval_secret_is_configured(settings):
        raise MutationPolicyError(operation, "approval secret is not securely configured")
    if not approval_secret_matches(settings, approval_secret):
        raise MutationPolicyError(operation, "approval secret is invalid")


def mutation_policy_snapshot(settings: Settings) -> dict[str, Any]:
    secret_ready = approval_secret_is_configured(settings)
    return {
        "fail_closed": True,
        "demo_is_simulation_only": True,
        "external_mutations_enabled": settings.tools_is_mutation_enabled,
        "human_approval_required": settings.human_approval_required,
        "approval_secret_configured": secret_ready,
        "external_mutations_allowed": bool(
            not settings.demo_mode
            and settings.tools_is_mutation_enabled
            and settings.human_approval_required
            and secret_ready
        ),
    }
