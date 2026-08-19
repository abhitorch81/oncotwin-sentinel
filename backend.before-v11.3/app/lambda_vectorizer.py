# OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class VectorizerError(RuntimeError):
    """Raised when the AWS Lambda memory worker cannot complete a request."""


def invoke_memory_vectorizer(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.memory_vectorizer_url or not settings.memory_vectorizer_token:
        raise VectorizerError("Memory vectorizer is not configured")

    request_body = {"action": action, **payload}
    try:
        response = httpx.post(
            settings.memory_vectorizer_url,
            headers={
                "X-OncoTwin-Token": settings.memory_vectorizer_token,
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=settings.memory_vectorizer_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise VectorizerError("Memory vectorizer request failed") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise VectorizerError("Memory vectorizer returned a non-JSON response") from exc

    if response.status_code >= 400:
        message = result.get("error", "Memory vectorizer rejected the request")
        raise VectorizerError(str(message))
    return result
