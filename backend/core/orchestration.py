"""End-to-end pipeline: voice/image/text -> diagnosis -> localized voice reply.

This is the single domain entry point the UI calls. It sequences the live
provider clients, applies safety post-processing, and assembles the dealer
list. Provider failures surface as honest notices to the farmer.
"""

from __future__ import annotations

from backend.core.errors import ProviderError
from backend.core.logging_utils import get_logger
from backend.core.models import AnalyzeRequest, AnalyzeResult, Diagnosis, Severity, Subject
from backend.core.safety import apply_safety
from backend.services import dealers as dealers_service
from backend.services import nemotron_client, stt_client, tiny_aya_client, tts_client

log = get_logger("core.orchestration")


def _notice(req: AnalyzeRequest, transcript: str, condition: str, message: str) -> AnalyzeResult:
    """Build a no-diagnosis result that shows the farmer an honest message."""

    diagnosis = Diagnosis(
        subject=Subject.UNKNOWN,
        condition=condition,
        severity=Severity.UNKNOWN,
        confidence=0.0,
        treatment="",
        prevention="",
    )
    return AnalyzeResult(
        transcript=transcript,
        language=req.language,
        diagnosis=diagnosis,
        localized_message=message,
        audio_reply_path=None,
        dealers=[],
        low_confidence=True,
    )


def analyze(req: AnalyzeRequest) -> AnalyzeResult:
    """Run the full assistant pipeline for one farmer request.

    Steps: transcribe the recording (or take typed text), forward-translate to
    English, diagnose with the omni model + optional image, gate for safety,
    localize, synthesize a spoken reply, and attach nearby dealers.
    """

    # 1) Source text — transcribe the farmer's recording, or take typed text.
    transcript = ""
    if req.audio_path:
        try:
            transcript = stt_client.transcribe(req.audio_path, req.language)
        except ProviderError:
            log.info("analyze op=pipeline path=stt_error")
            return _notice(
                req,
                "",
                "Audio not understood",
                "We couldn't process your voice message. Please re-record "
                "clearly, or type your symptoms.",
            )
    else:
        transcript = (req.text or "").strip()

    if not transcript and not req.image_path:
        log.info("analyze op=pipeline path=empty")
        return _notice(
            req,
            "",
            "No input",
            "Please record a voice message, type the symptoms, or add a photo "
            "of the crop or animal.",
        )

    # 2) Forward-translate to English (the diagnosis model is weak in Swahili),
    #    then 3) diagnose. Both the translate and diagnose calls are live.
    try:
        symptom_en = tiny_aya_client.translate_to_english(transcript, req.language)
        raw = nemotron_client.diagnose(symptom_en, req.image_path)
    except ProviderError:
        log.info("analyze op=pipeline path=diagnosis_error")
        return _notice(
            req,
            transcript,
            "Service busy",
            "The diagnosis service is unavailable right now. Please try again "
            "in a moment.",
        )

    # 4) Safety gating (low-confidence fallback, escalation flags).
    diagnosis, low_confidence = apply_safety(raw)

    # 5) Localize to the farmer's language (degrades to English on failure).
    message = tiny_aya_client.localize(diagnosis, req.language)

    # 6) Spoken reply.
    audio_reply = tts_client.synthesize(message, req.language)

    # 7) Nearby dealers (only when we have a usable diagnosis). GPS coordinates,
    #    when shared, rank dealers by real distance from the farmer.
    found = (
        []
        if low_confidence
        else dealers_service.find_nearby(county=req.county, lat=req.lat, lon=req.lon)
    )

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
