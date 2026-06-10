from unittest.mock import patch

from backend.core.models import AnalyzeResult, Diagnosis, Severity, Subject
from frontend.app_ui import (
    _captured_image_state,
    _diagnose_button_state,
    _on_submit,
    build_ui,
)


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
        response, audio, user_text, user_image, text, voice, image = _on_submit(
            "en", None, None, "brown spots", None, None, None
        )

    assert "Possible leaf spot" in response
    assert "Nearby agro-dealers" in response
    assert "_No dealer suggestions for this result._" in response
    assert audio == "/tmp/reply.mp3"
    assert user_text == "brown spots"
    assert user_image["value"] is None
    assert user_image["visible"] is False
    assert text == ""
    assert voice is None
    assert image["value"] is None
    assert image["visible"] is False


def test_submit_passes_recorded_audio_path_to_pipeline() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()) as analyze:
        values = _on_submit("sw", "/tmp/voice.wav", None, None, None, None, None)

    assert analyze.call_args.args[0].audio_path == "/tmp/voice.wav"
    assert analyze.call_args.args[0].language == "sw"
    assert values[2] == "My maize leaves have brown spots."


def test_submitted_image_is_preserved_in_user_message() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()):
        values = _on_submit(
            "en", None, "/tmp/crop.jpg", "brown spots", None, None, None
        )

    assert values[3]["value"] == "/tmp/crop.jpg"
    assert values[3]["visible"] is True


def test_captured_image_is_preserved_when_camera_closes() -> None:
    selected_image, camera = _captured_image_state("/tmp/camera.jpg")

    assert selected_image["value"] == "/tmp/camera.jpg"
    assert selected_image["visible"] is True
    assert camera["visible"] is False
    assert "value" not in camera


def test_build_ui_creates_blocks() -> None:
    assert build_ui() is not None


def test_photo_menu_uses_compact_upload_and_camera_controls() -> None:
    ui = build_ui()
    images = [
        component
        for component in ui.blocks.values()
        if component.__class__.__name__ == "Image"
    ]
    upload_buttons = [
        component
        for component in ui.blocks.values()
        if component.__class__.__name__ == "UploadButton"
    ]

    assert len(images) == 3
    assert [image.sources for image in images].count(["webcam"]) == 1
    assert len(upload_buttons) == 1
    assert upload_buttons[0].file_types == ["image"]


def test_diagnose_button_requires_non_whitespace_text() -> None:
    assert _diagnose_button_state(None)["interactive"] is False
    assert _diagnose_button_state("")["interactive"] is False
    assert _diagnose_button_state("   ")["interactive"] is False
    assert _diagnose_button_state("brown spots")["interactive"] is True


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
