"""Speech-to-text for Swahili (Path A: Whisper large-v3, or fine-tuned MMS).

NOTE: Cohere Transcribe was dropped from the original plan because it does
not support Swahili or Dholuo. Swahili works off-the-shelf with Whisper/MMS;
a fine-tuned checkpoint can replace ``ASR_MODEL`` later for the Well-Tuned
badge without touching callers.
"""

from __future__ import annotations

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.stt")

# Deterministic stub transcripts so the demo flow runs without model weights.
_STUB_BY_LANG: dict[Language, str] = {
    "sw": "Majani ya mahindi yangu yana madoa ya manjano na yanakauka.",
    "luo": "It bel mara nigi range ma rachar kendo gidwogo motwo.",
    "en": "My maize leaves have yellow spots and are drying up.",
}


def _transcribe_stub(language: Language) -> str:
    log.info("transcribe stub op=stt lang=%s", language)
    return _STUB_BY_LANG.get(language, _STUB_BY_LANG["sw"])


def transcribe(audio_path: str, language: Language = "sw") -> str:
    """Transcribe a voice message to text in its source language.

    Returns the recognised text. On the stub path it returns a representative
    sample so the rest of the pipeline can be exercised end-to-end.
    """

    if not settings.use_real_stt:
        return _transcribe_stub(language)

    # TODO(real): call HF Inference / local Whisper or MMS with ASR_MODEL.
    #   from huggingface_hub import InferenceClient
    #   client = InferenceClient(model=settings.asr_model, token=settings.hf_token)
    #   return client.automatic_speech_recognition(audio_path).text
    log.warning("transcribe op=stt real_not_wired=1 fallback=stub")
    return _transcribe_stub(language)
