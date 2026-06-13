"""End-to-end pipeline: voice/image/text -> diagnosis -> localized voice reply.

This is the single domain entry point the UI calls. It sequences the live
provider clients, applies safety post-processing, and assembles the dealer
list. Provider failures surface as honest notices to the farmer.
"""

from __future__ import annotations

from backend.core.errors import ProviderError
from backend.core.geolocation import resolve_location
from backend.core.logging_utils import get_logger
from backend.core.models import AnalyzeRequest, AnalyzeResult, Diagnosis, Severity, Subject
from backend.core.safety import apply_safety
from backend.services import (
    google_places,
    nemotron_client,
    openai_vision_client,
    stt_client,
    tiny_aya_client,
    tts_client,
)

log = get_logger("core.orchestration")


def _message(req: AnalyzeRequest, english: str, swahili: str) -> str:
    """Choose fixed operational copy in the farmer's selected language."""

    return swahili if req.language == "sw" else english


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
    English, diagnose with the omni model + optional GPT-5.4 image fallback,
    gate for safety, localize, synthesize a spoken reply, and attach nearby
    dealers.
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
                _message(
                    req,
                    "We couldn't process your voice message. Please re-record "
                    "clearly, or type your symptoms.",
                    "Hatukuweza kuchakata ujumbe wako wa sauti. Tafadhali rekodi "
                    "tena kwa uwazi au andika dalili.",
                ),
            )
    else:
        transcript = (req.text or "").strip()

    if not transcript and not req.image_path:
        log.info("analyze op=pipeline path=empty")
        return _notice(
            req,
            "",
            "No input",
            _message(
                req,
                "Please record a voice message, type the symptoms, or add a photo "
                "of the crop or animal.",
                "Tafadhali rekodi ujumbe wa sauti, andika dalili, au ongeza picha "
                "ya zao au mnyama.",
            ),
        )

    # 2) Forward-translate to English (the diagnosis model is weak in Swahili),
    #    then 3) diagnose. Both the translate and diagnose calls are live.
    symptom_en = tiny_aya_client.translate_to_english(transcript, req.language)
    try:
        raw = nemotron_client.diagnose(symptom_en, req.image_path)
    except ProviderError:
        if req.image_path:
            try:
                log.warning("analyze op=pipeline path=openai_vision_fallback")
                raw = openai_vision_client.diagnose(symptom_en, req.image_path)
            except ProviderError:
                log.info("analyze op=pipeline path=diagnosis_error")
                return _notice(
                    req,
                    transcript,
                    "Service busy",
                    _message(
                        req,
                        "The diagnosis service is unavailable right now. Please try "
                        "again in a moment.",
                        "Huduma ya utambuzi haipatikani kwa sasa. Tafadhali jaribu "
                        "tena baada ya muda mfupi.",
                    ),
                )
        else:
            log.info("analyze op=pipeline path=diagnosis_error")
            return _notice(
                req,
                transcript,
                "Service busy",
                _message(
                    req,
                    "The diagnosis service is unavailable right now. Please try "
                    "again in a moment.",
                    "Huduma ya utambuzi haipatikani kwa sasa. Tafadhali jaribu tena "
                    "baada ya muda mfupi.",
                ),
            )

    # 4) Safety gating (low-confidence fallback, escalation flags).
    diagnosis, low_confidence = apply_safety(raw)

    # 5) Required nearby-agrovet tool call for a usable diagnosis using browser GPS.
    found = []
    dealer_status = "not_requested"
    dealer_radius = None
    disease_identified = (
        not low_confidence
        and diagnosis.subject != Subject.UNKNOWN
        and diagnosis.condition.strip().lower() not in {"", "unclear", "unknown"}
    )
    if disease_identified:
        try:
            location = resolve_location(req.lat, req.lon)
            if location is None:
                dealer_status = "location_required"
            else:
                found, dealer_radius = google_places.search_nearby_agrovets(*location)
                dealer_status = "success" if found else "no_results"
        except ProviderError:
            dealer_status = "error"
            log.warning("analyze op=agrovet_search ok=0")

    # 6) Localize to the farmer's language (degrades to English on failure).
    localized_condition = (
        tiny_aya_client.localize_condition(diagnosis.condition, req.language)
        if disease_identified
        else None
    )
    message = tiny_aya_client.localize(diagnosis, req.language)

    # 7) Spoken reply.
    audio_reply = tts_client.synthesize(message, req.language)

    log.info(
        "analyze op=pipeline path=full low=%s dealer_status=%s",
        low_confidence,
        dealer_status,
    )
    return AnalyzeResult(
        transcript=transcript,
        language=req.language,
        diagnosis=diagnosis,
        localized_message=message,
        localized_condition=localized_condition,
        audio_reply_path=audio_reply,
        dealers=found,
        dealer_search_status=dealer_status,
        dealer_search_radius_km=dealer_radius,
        low_confidence=low_confidence,
    )
