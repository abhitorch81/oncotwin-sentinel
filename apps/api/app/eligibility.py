"""Truthful, non-billable eligibility proof for the Google technology requirements."""

import re
from typing import Any


MINIMUM_GEMINI_VERSION = (3, 5)
_VERSION_PATTERN = re.compile(r"^gemini-(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:[-.]|$)")


def gemini_version(model: str) -> tuple[int, int] | None:
    match = _VERSION_PATTERN.match(model.strip().lower())
    if not match:
        return None
    return int(match.group("major")), int(match.group("minor") or 0)


def meets_minimum_gemini_version(model: str) -> bool:
    version = gemini_version(model)
    return version is not None and version >= MINIMUM_GEMINI_VERSION


def build_eligibility_proof(
    *,
    model: str,
    vertex_ai_enabled: bool,
    adk_status: dict[str, Any],
    firestore_configured: bool,
    cloud_run_target: bool,
) -> dict[str, Any]:
    model_requirement = meets_minimum_gemini_version(model) and vertex_ai_enabled
    framework_requirement = bool(adk_status.get("installed") and adk_status.get("enabled"))
    infrastructure_services = [
        service
        for service, enabled in (("Cloud Run", cloud_run_target), ("Firestore", firestore_configured))
        if enabled
    ]
    infrastructure_requirement = bool(infrastructure_services)
    return {
        "requirements_met": model_requirement and framework_requirement and infrastructure_requirement,
        "gemini": {
            "requirement": "Gemini 3.5 or newer through Gemini API or Vertex AI",
            "model": model,
            "minimum_version_met": meets_minimum_gemini_version(model),
            "access": "vertex_ai" if vertex_ai_enabled else "unverified",
            "configured": model_requirement,
        },
        "agent_framework": {
            "requirement": "At least one Google Agent Framework",
            "name": "Google ADK",
            "version": adk_status.get("version"),
            "workflow": adk_status.get("workflow"),
            "configured": framework_requirement,
        },
        "google_cloud_infrastructure": {
            "requirement": "At least one Google Cloud infrastructure service",
            "services": infrastructure_services,
            "configured": infrastructure_requirement,
        },
        "proof_scope": "configuration_only_no_model_call",
    }
