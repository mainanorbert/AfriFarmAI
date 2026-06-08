"""End-to-end pipeline: voice/image/text -> diagnosis -> localized voice reply.

This is the single domain entry point the UI calls. It sequences the provider
clients, applies safety post-processing, and assembles the dealer list.
"""

from __future__ import annotations

from backend.core.logging_utils import get_logger
from backend.core.models import AnalyzeRequest, AnalyzeResult, Diagnosis, Severity, Subject
from backend.core.safety import apply_safety
from backend.services import dealers as dealers_service
from backend.services import nemotron_client, stt_client, tiny_aya_client, tts_client

log = get_logger("core.orchestration")


def analyze(req: AnalyzeRequest) -> AnalyzeResult:
    """Run the full assistant pipeline for one farmer request.

    Steps: (1) transcribe voice or take typed text, (2) diagnose with the omni
    model from text + optional image, (3) apply safety gating, (4) localize,
    (5) synthesize a spoken reply, (6) attach nearby dealers.
    """

    # 1) Source text — prefer a voice message, fall back to typed text.
    if req.audio_path:
        transcript = stt_client.transcribe(req.audio_path, req.language)
    else:
        transcript = (req.text or "").strip()

    if not transcript and not req.image_path:
        # Nothing to work with: return a cautious, low-confidence result.
        empty = Diagnosis(
            subject=Subject.UNKNOWN,
            condition="No input",
            severity=Severity.UNKNOWN,
            confidence=0.0,
            treatment="",
            prevention="",
        )
        diagnosis, low = apply_safety(empty)
        message = tiny_aya_client.localize(diagnosis, req.language)
        log.info("analyze op=pipeline path=empty")
        return AnalyzeResult(
            transcript=transcript,
            language=req.language,
            diagnosis=diagnosis,
            localized_message=message,
            audio_reply_path=None,
            dealers=[],
            low_confidence=low,
        )

    # 2) Diagnose (omni model handles image + reasoning together).
    raw = nemotron_client.diagnose(transcript, req.image_path)

    # 3) Safety gating (low-confidence fallback, escalation flags).
    diagnosis, low_confidence = apply_safety(raw)

    # 4) Localize to the farmer's language.
    message = tiny_aya_client.localize(diagnosis, req.language)

    # 5) Spoken reply.
    audio_reply = tts_client.synthesize(message, req.language)

    # 6) Nearby dealers (only when we have a usable diagnosis).
    found = [] if low_confidence else dealers_service.find_nearby(county=req.county)

    log.info("analyze op=pipeline path=full low=%s", low_confidence)
    return AnalyzeResult(
        transcript=transcript,
        language=req.language,
        diagnosis=diagnosis,
        localized_message=message,
        audio_reply_path=audio_reply,
        dealers=found,
        low_confidence=low_confidence,
    )
