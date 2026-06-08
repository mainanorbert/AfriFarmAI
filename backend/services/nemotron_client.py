"""Diagnosis reasoning + image understanding via Nemotron 3 Nano Omni.

In Path A this single 30B-A3B omni model handles the crop/animal image *and*
the symptom reasoning, so no separate vision model is required. The stub maps
common symptom keywords to representative diagnoses so the demo is responsive.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from typing import Any, Optional

import requests

from backend.core.config import settings
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
    "chemicals."
)

# Minimal keyword → diagnosis map for the stub path (English/Swahili cues).
_RULES: list[tuple[tuple[str, ...], Diagnosis]] = [
    (
        ("mahindi", "maize", "bel", "madoa", "spot", "manjano", "yellow"),
        Diagnosis(
            subject=Subject.CROP,
            condition="Maize Lethal Necrosis (MLN)",
            severity=Severity.MODERATE,
            confidence=0.72,
            treatment=(
                "Remove and destroy badly affected plants. Control insect "
                "vectors (thrips, aphids) with an approved insecticide and "
                "avoid moving infected material between fields."
            ),
            prevention=(
                "Plant certified disease-free seed, rotate with non-cereal "
                "crops, and keep fields weed-free to reduce vectors."
            ),
        ),
    ),
    (
        ("worm", "funza", "kiwavi", "holes", "mashimo"),
        Diagnosis(
            subject=Subject.CROP,
            condition="Fall Armyworm",
            severity=Severity.MODERATE,
            confidence=0.69,
            treatment=(
                "Scout early; apply an approved biopesticide or insecticide "
                "into the leaf whorl in the evening. Handpick egg masses where "
                "feasible."
            ),
            prevention=(
                "Plant early and uniformly, intercrop with legumes, and "
                "encourage natural predators."
            ),
        ),
    ),
    (
        ("ng'ombe", "cow", "cattle", "diho", "homa", "fever", "animal"),
        Diagnosis(
            subject=Subject.ANIMAL,
            condition="Suspected East Coast Fever",
            severity=Severity.SEVERE,
            confidence=0.66,
            treatment=(
                "This can be fatal quickly. Contact a veterinarian urgently. "
                "Keep the animal shaded and hydrated while you arrange care."
            ),
            prevention=(
                "Control ticks with regular dipping/spraying and consider "
                "vaccination where available."
            ),
            escalate=True,
        ),
    ),
]

_DEFAULT = Diagnosis(
    subject=Subject.UNKNOWN,
    condition="Unclear",
    severity=Severity.UNKNOWN,
    confidence=0.30,
    treatment="",
    prevention="",
)


def diagnose(symptom_text: str, image_path: Optional[str] = None) -> Diagnosis:
    """Produce a structured diagnosis from symptom text and optional image.

    The omni model is multimodal; on the stub path the image is acknowledged
    but the match is driven by symptom keywords for determinism.
    """

    if not settings.use_real_nemotron:
        return _diagnose_stub(symptom_text, image_path)
    return _diagnose_real(symptom_text, image_path)


def _diagnose_stub(symptom_text: str, image_path: Optional[str]) -> Diagnosis:
    """Keyword-driven diagnosis used when real models are disabled."""

    has_image = bool(image_path)
    haystack = symptom_text.lower()
    for keywords, diagnosis in _RULES:
        if any(k in haystack for k in keywords):
            log.info("diagnose stub op=reason matched=1 image=%s", has_image)
            # An accompanying image nudges confidence up slightly.
            if has_image:
                return diagnosis.model_copy(
                    update={"confidence": min(diagnosis.confidence + 0.08, 0.95)}
                )
            return diagnosis
    log.info("diagnose stub op=reason matched=0 image=%s", has_image)
    return _DEFAULT


def _diagnose_real(symptom_text: str, image_path: Optional[str]) -> Diagnosis:
    """Call Nemotron Omni and parse a structured diagnosis.

    Any failure (missing key, network, bad JSON) degrades to a low-confidence
    default so the safety layer produces a cautious fallback rather than the UI
    crashing.
    """

    if not settings.nvidia_api_key:
        log.error("diagnose op=reason error=missing_api_key")
        return _DEFAULT

    try:
        content = _call_nemotron(symptom_text, image_path)
    except requests.RequestException:
        # No request content logged, per privacy guardrails.
        log.error("diagnose op=reason error=request_failed")
        return _DEFAULT

    data = _extract_json(content)
    if data is None:
        log.error("diagnose op=reason error=unparseable_response")
        return _DEFAULT

    diagnosis = _to_diagnosis(data)
    log.info(
        "diagnose op=reason matched=1 image=%s conf=%.2f",
        bool(image_path),
        diagnosis.confidence,
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
