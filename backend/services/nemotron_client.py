"""Diagnosis reasoning + image understanding via Nemotron 3 Nano Omni.

This single 30B-A3B omni model handles the crop/animal image *and* the symptom
reasoning, so no separate vision model is required. Always live: any failure
raises :class:`ProviderError` rather than returning canned data.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from typing import Any, Optional

import requests

from backend.core.config import settings
from backend.core.errors import ProviderError
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis, Severity, Subject

log = get_logger("services.nemotron")

# Instruction that pins the model to a strict, cautious JSON contract.
_SYSTEM_PROMPT = (
    "You are an agricultural and veterinary diagnostic assistant for "
    "smallholder farmers in Kenya. The farmer's symptom description may be in "
    "Swahili, Dholuo, or English, and may include a photo of a crop or animal. "
    "Identify the single most likely problem.\n\n"
    "Respond with ONLY one JSON object — no prose, no markdown fences — with "
    "exactly these keys:\n"
    '  "subject": "crop" | "animal" | "unknown"\n'
    '  "condition": short English name of the likely disease/pest/condition\n'
    '  "severity": "mild" | "moderate" | "severe" | "unknown"\n'
    '  "confidence": number between 0 and 1\n'
    '  "treatment": practical, safe steps (include safe-handling notes)\n'
    '  "prevention": practical prevention guidance\n'
    '  "escalate": true if a vet/agronomist should be consulted urgently\n\n'
    "If the farmer names a specific crop or animal (e.g. maize/mahindi, "
    "cattle/ng'ombe), your diagnosis MUST be consistent with that crop or "
    "animal — do not diagnose a condition of a different species.\n"
    "Be cautious. If the input is unclear or you are unsure, use low "
    "confidence and \"unknown\" fields. Never recommend banned or unsafe "
    "chemicals. When a disease is confidently identified, the application "
    "must run its required nearby-agrovet search tool before presenting the "
    "final response; never invent dealer names or contact details."
)

def diagnose(symptom_text: str, image_path: Optional[str] = None) -> Diagnosis:
    """Produce a structured diagnosis from symptom text and optional image.

    Always calls the live omni model. Raises :class:`ProviderError` on a missing
    key, network failure, or unparseable response.
    """

    if not settings.nvidia_api_key:
        raise ProviderError("diagnosis", "missing NVIDIA key")

    try:
        content = _call_nemotron(symptom_text, image_path)
    except requests.RequestException as exc:
        # No request content logged, per privacy guardrails.
        log.error("diagnose op=reason error=request_failed")
        raise ProviderError("diagnosis") from exc

    data = _extract_json(content)
    if data is None:
        log.error("diagnose op=reason error=unparseable_response")
        raise ProviderError("diagnosis", "unparseable response")

    diagnosis = _to_diagnosis(data)
    log.info(
        "diagnose op=reason image=%s conf=%.2f", bool(image_path), diagnosis.confidence
    )
    return diagnosis


def _encode_image_data_uri(image_path: str) -> str:
    """Read an image file and return a base64 ``data:`` URI for the API."""

    mime, _ = mimetypes.guess_type(image_path)
    mime = mime if (mime and mime.startswith("image/")) else "image/jpeg"
    with open(image_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _call_nemotron(symptom_text: str, image_path: Optional[str]) -> str:
    """POST the chat-completions request and return the raw message content."""

    user_content: list[dict[str, Any]] = []
    if symptom_text.strip():
        user_content.append({"type": "text", "text": symptom_text.strip()})
    else:
        user_content.append(
            {"type": "text", "text": "Diagnose the problem shown in this photo."}
        )
    if image_path:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": _encode_image_data_uri(image_path)},
            }
        )

    payload = {
        "model": settings.nemotron_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 2048,
        # Low temperature for deterministic, schema-faithful output.
        "temperature": 0.2,
        "top_p": 0.95,
        # Force a pure-JSON response (no prose/fences) and disable reasoning so
        # the answer is not truncated by chain-of-thought.
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        f"{settings.nemotron_base_url}/chat/completions",
        json=payload,
        headers=headers,
        timeout=settings.provider_timeout_seconds,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    """Pull a JSON object from model output, tolerating reasoning and fences."""

    # Drop any chain-of-thought left in the response.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        candidate = text[start : end + 1] if 0 <= start < end else None

    if not candidate:
        return None
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _coerce_enum(value: Any, enum_cls, default):
    """Map a raw string to an enum member, falling back to ``default``."""

    try:
        return enum_cls(str(value).strip().lower())
    except (ValueError, AttributeError):
        return default


def _to_diagnosis(data: dict[str, Any]) -> Diagnosis:
    """Validate and coerce the model's JSON into a Diagnosis, never raising."""

    try:
        confidence = float(data.get("confidence", 0.3))
    except (TypeError, ValueError):
        confidence = 0.3
    confidence = max(0.0, min(confidence, 1.0))

    return Diagnosis(
        subject=_coerce_enum(data.get("subject"), Subject, Subject.UNKNOWN),
        condition=str(data.get("condition") or "Unclear").strip(),
        severity=_coerce_enum(data.get("severity"), Severity, Severity.UNKNOWN),
        confidence=confidence,
        treatment=str(data.get("treatment") or "").strip(),
        prevention=str(data.get("prevention") or "").strip(),
        escalate=bool(data.get("escalate", False)),
    )
