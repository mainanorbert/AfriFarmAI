"""GPT-5.4 fallback for image-backed agricultural diagnoses."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError
from pydantic import ValidationError

from backend.core.config import settings
from backend.core.errors import ProviderError
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis

log = get_logger("services.openai_vision")

_INSTRUCTIONS = (
    "Analyze the supplied crop or livestock photo and symptom description as "
    "agricultural decision support for a smallholder farmer in Kenya. Identify "
    "only the single most likely visible disease, pest, or health condition. "
    "Be cautious: if the photo is unclear, unrelated, or insufficient for a "
    "reliable identification, return unknown fields and low confidence. Keep "
    "the diagnosis consistent with any crop or animal named by the farmer. "
    "Never recommend banned, unsafe, or unverified treatments. Include safe "
    "handling guidance and escalate severe, urgent, uncertain, animal, or "
    "worsening cases to a veterinarian, agronomist, or extension officer."
)

_DIAGNOSIS_FORMAT = {
    "type": "json_schema",
    "name": "agricultural_diagnosis",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "enum": ["crop", "animal", "unknown"]},
            "condition": {"type": "string"},
            "severity": {
                "type": "string",
                "enum": ["mild", "moderate", "severe", "unknown"],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "treatment": {"type": "string"},
            "prevention": {"type": "string"},
            "escalate": {"type": "boolean"},
        },
        "required": [
            "subject",
            "condition",
            "severity",
            "confidence",
            "treatment",
            "prevention",
            "escalate",
        ],
        "additionalProperties": False,
    },
}


def diagnose(symptom_text: str, image_path: str) -> Diagnosis:
    """Analyze an image with GPT-5.4 and return a validated diagnosis."""

    if not settings.openai_api_key:
        log.error("diagnose op=vision_fallback error=missing_key")
        raise ProviderError("diagnosis", "missing OpenAI key")

    try:
        image_url = _encode_image_data_uri(image_path)
        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.provider_timeout_seconds,
        )
        response = client.responses.create(
            model=settings.openai_vision_model,
            instructions=_INSTRUCTIONS,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": symptom_text.strip()
                            or "Identify the problem visible in this photo.",
                        },
                        {
                            "type": "input_image",
                            "image_url": image_url,
                            "detail": "original",
                        },
                    ],
                }
            ],
            reasoning={"effort": "medium"},
            text={"format": _DIAGNOSIS_FORMAT},
            max_output_tokens=1200,
            store=False,
        )
        diagnosis = Diagnosis.model_validate(json.loads(response.output_text))
    except (OpenAIError, OSError, json.JSONDecodeError, ValidationError, TypeError) as exc:
        error, status, request_id = _safe_error_context(exc)
        log.error(
            "diagnose op=vision_fallback error=%s status=%s request_id=%s",
            error,
            status,
            request_id,
        )
        raise ProviderError("diagnosis", "OpenAI vision fallback failed") from exc

    log.info("diagnose op=vision_fallback ok=1 conf=%.2f", diagnosis.confidence)
    return diagnosis


def _safe_error_context(exc: Exception) -> tuple[str, str, str]:
    """Return privacy-safe provider diagnostics without response content."""

    if isinstance(exc, APIStatusError):
        return (
            "status_error",
            str(exc.status_code),
            str(getattr(exc, "request_id", None) or "unknown"),
        )
    if isinstance(exc, APITimeoutError):
        return "timeout", "none", "unknown"
    if isinstance(exc, APIConnectionError):
        return "connection_error", "none", "unknown"
    if isinstance(exc, OSError):
        return "image_file_error", "none", "unknown"
    return "invalid_response", "none", "unknown"


def _encode_image_data_uri(image_path: str) -> str:
    """Read a supported local image and return a base64 data URL."""

    path = Path(image_path)
    mime, _ = mimetypes.guess_type(path.name)
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
        raise OSError("unsupported image type")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
