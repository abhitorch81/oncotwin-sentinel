from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .models import ImageEvidenceAnalysis, Mission, PriorReceiptComparison, ScenePatch

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


class _VisualFinding(BaseModel):
    synthetic_pattern: Literal[
        "diffuse", "clustered", "ring_like", "heterogeneous", "low_signal"
    ]
    r7_similarity: float = Field(ge=0, le=1)
    matrix_resistance_signal: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=500)
    spoken_text: str = Field(min_length=1, max_length=700)
    observations: list[str] = Field(min_length=1, max_length=5)
    prior_receipt_comparisons: list[PriorReceiptComparison] = Field(max_length=3)


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(data: bytes, claimed_type: str) -> str:
    if not data:
        raise ValueError("The synthetic image is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Synthetic images must be 5 MB or smaller")
    detected = detect_image_type(data)
    if claimed_type not in ALLOWED_IMAGE_TYPES or detected != claimed_type:
        raise ValueError("Upload a valid PNG, JPEG, or WebP synthetic image")
    return detected


def safe_filename(filename: str | None, mime_type: str) -> str:
    fallback = {"image/png": "evidence.png", "image/jpeg": "evidence.jpg", "image/webp": "evidence.webp"}[mime_type]
    name = Path(filename or fallback).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return (cleaned or fallback)[:120]


def _mission_context(mission: Mission, selected_candidate_id: str | None, hour: int) -> dict[str, Any]:
    receipt = mission.receipt
    if receipt is None:
        raise ValueError("Mission evidence receipt is unavailable")
    selected = next(
        (result for result in receipt.results if result.candidate.id == selected_candidate_id),
        None,
    )
    frame = next(
        (item for item in receipt.timeline if item.candidate_id == selected_candidate_id and item.hour == hour),
        None,
    )
    return {
        "mission_id": mission.id,
        "selected_candidate": selected.model_dump(mode="json") if selected else None,
        "simulation_frame": frame.model_dump(mode="json") if frame else None,
        "preferred_candidate_id": receipt.preferred_candidate_id,
        "rejected_candidate_ids": receipt.rejected_candidate_ids,
        "current_receipt_sha256_prefix": receipt.receipt_sha256[:12],
    }


def analyze_synthetic_image(
    *,
    data: bytes,
    filename: str | None,
    mime_type: str,
    mission: Mission,
    selected_candidate_id: str | None,
    simulation_hour: int,
    prior_receipts: list[dict[str, Any]],
    project_id: str,
    location: str,
    model: str,
    client: Any | None = None,
    types_module: Any | None = None,
) -> ImageEvidenceAnalysis:
    detected_type = validate_image(data, mime_type)
    digest = hashlib.sha256(data).hexdigest()
    evidence_id = f"IMG-{digest[:12].upper()}"
    context = _mission_context(mission, selected_candidate_id, simulation_hour)
    prompt = """You are the Evidence Scout in a synthetic research-only nanoparticle digital twin.
Analyze the attached synthetic microscopy-like image. Do not diagnose disease, identify a real patient,
recommend treatment, or infer clinical outcomes. Describe only bounded visual patterns. Compare those
patterns with the selected synthetic candidate/time context and the privacy-safe prior receipt summaries.
Return JSON matching this exact shape: synthetic_pattern (diffuse|clustered|ring_like|heterogeneous|low_signal),
r7_similarity (0..1), matrix_resistance_signal (0..1), confidence (0..1), summary, spoken_text,
observations (1..5 short strings), prior_receipt_comparisons (0..3 objects containing
receipt_sha256_prefix, relationship consistent|divergent|insufficient_signal, and summary).
Never claim approval authority. If prior context is weak, use insufficient_signal.

CONTEXT:
""" + json.dumps({"current": context, "prior_receipts": prior_receipts}, separators=(",", ":"))

    if client is None:
        from google import genai

        client = genai.Client(vertexai=True, project=project_id, location=location)
    if types_module is None:
        from google.genai import types as types_module

    response = client.models.generate_content(
        model=model,
        contents=[prompt, types_module.Part.from_bytes(data=data, mime_type=detected_type)],
        config=types_module.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned no visual evidence result")
    finding = _VisualFinding.model_validate_json(response.text)
    allowed_prefixes = {item.get("receipt_sha256_prefix") for item in prior_receipts}
    comparisons = [
        item for item in finding.prior_receipt_comparisons
        if item.receipt_sha256_prefix in allowed_prefixes
    ][:3]
    return ImageEvidenceAnalysis(
        mission_id=mission.id,
        evidence_id=evidence_id,
        sha256=digest,
        filename=safe_filename(filename, detected_type),
        mime_type=detected_type,
        size_bytes=len(data),
        model=model,
        selected_candidate_id=selected_candidate_id,
        simulation_hour=simulation_hour,
        synthetic_pattern=finding.synthetic_pattern,
        r7_similarity=finding.r7_similarity,
        matrix_resistance_signal=finding.matrix_resistance_signal,
        confidence=finding.confidence,
        summary=finding.summary,
        spoken_text=finding.spoken_text,
        observations=finding.observations,
        prior_receipt_comparisons=comparisons,
        current_receipt_sha256_prefix=context["current_receipt_sha256_prefix"],
        scene_patch=ScenePatch(
            action="focus_clone", camera_target="clone_r7", overlay="clone_signal",
            candidate_ids=[selected_candidate_id] if selected_candidate_id else [],
            simulation_hour=simulation_hour, emphasis="evidence",
        ),
    )
