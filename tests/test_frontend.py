from unittest.mock import patch

from backend.core.models import AnalyzeResult, Diagnosis, Severity, Subject
from frontend.app_ui import _on_submit, build_ui


def _result() -> AnalyzeResult:
    return AnalyzeResult(
        transcript="My maize leaves have brown spots.",
        language="en",
        diagnosis=Diagnosis(
            subject=Subject.CROP,
            condition="Possible leaf spot",
            severity=Severity.MODERATE,
            confidence=0.72,
            treatment="Remove badly affected leaves.",
            prevention="Avoid wetting leaves.",
        ),
        localized_message="Remove badly affected leaves and monitor the crop.",
        audio_reply_path="/tmp/reply.mp3",
    )


def test_submit_returns_one_unified_response() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()):
        response, audio, text, voice, image = _on_submit(
            "en", None, None, "brown spots", None, None, None
        )

    assert "My maize leaves have brown spots." in response
    assert "Possible leaf spot" in response
    assert "Nearby agro-dealers" in response
    assert "_No dealer suggestions for this result._" in response
    assert audio == "/tmp/reply.mp3"
    assert (text, voice, image) == ("", None, None)


def test_submit_passes_recorded_audio_path_to_pipeline() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()) as analyze:
        _on_submit("sw", "/tmp/voice.wav", None, None, None, None, None)

    assert analyze.call_args.args[0].audio_path == "/tmp/voice.wav"
    assert analyze.call_args.args[0].language == "sw"


def test_build_ui_creates_blocks() -> None:
    assert build_ui() is not None


def test_swahili_response_uses_localized_message_and_labels() -> None:
    result = _result().model_copy(
        update={
            "language": "sw",
            "localized_message": "Ondoa majani yaliyoathirika.",
        }
    )

    from frontend.app_ui import _render_response

    response = _render_response(result)
    assert "Maelezo yako" in response
    assert "Ondoa majani yaliyoathirika." in response
    assert "Hakuna wauzaji waliopendekezwa" in response
    assert "Nearby agro-dealers" not in response
