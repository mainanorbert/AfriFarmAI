from unittest.mock import patch

import pytest
from pydantic import ValidationError

from backend.core.models import (
    AnalyzeRequest,
    AnalyzeResult,
    Dealer,
    Diagnosis,
    Severity,
    Subject,
)
from frontend.app_ui import (
    _captured_image_state,
    _dealer_pagination_updates,
    _diagnose_button_state,
    _next_dealer_page,
    _on_submit,
    _render_response,
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


def _dealers(count: int) -> list[Dealer]:
    return [
        Dealer(
            name=f"Agrovet {index}",
            address=f"Address {index}",
            rating=4.0,
            phone=f"+25470000000{index}",
            lat=-0.1,
            lon=34.7,
            distance_km=float(index),
            maps_link=f"https://maps.google.com/{index}",
        )
        for index in range(1, count + 1)
    ]


def test_submit_returns_one_unified_response() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()):
        values = _on_submit(
            "en", None, None, "brown spots", None, None
        )
    response, audio, user_text, user_image, text, voice, image = values[:7]

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
    assert values[7] == _result()
    assert values[8] == 0
    assert values[9]["visible"] is False


def test_submit_passes_recorded_audio_path_to_pipeline() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()) as analyze:
        values = _on_submit("sw", "/tmp/voice.wav", None, None, None, None)

    assert analyze.call_args.args[0].audio_path == "/tmp/voice.wav"
    assert analyze.call_args.args[0].language == "sw"
    assert values[2] == "My maize leaves have brown spots."


def test_submitted_image_is_preserved_in_user_message() -> None:
    with patch("frontend.app_ui.analyze", return_value=_result()):
        values = _on_submit(
            "en", None, "/tmp/crop.jpg", "brown spots", None, None
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


def test_language_choices_exclude_unsupported_dholuo() -> None:
    from frontend.strings import LANGUAGE_CHOICES

    assert LANGUAGE_CHOICES == [("Kiswahili", "sw"), ("English", "en")]
    with pytest.raises(ValidationError):
        AnalyzeRequest(language="luo", text="symptoms")


def test_location_retry_is_compact_and_manual_location_ui_is_absent() -> None:
    ui = build_ui()
    location_buttons = [
        component
        for component in ui.blocks.values()
        if component.__class__.__name__ == "Button"
        and getattr(component, "elem_classes", None) == ["location-toggle"]
    ]
    accordions = [
        component
        for component in ui.blocks.values()
        if component.__class__.__name__ == "Accordion"
    ]

    assert len(location_buttons) == 1
    assert location_buttons[0].min_width == 34
    assert accordions == []


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


def test_diagnose_button_requires_any_supported_input() -> None:
    assert _diagnose_button_state(None, None, None)["interactive"] is False
    assert _diagnose_button_state("", None, None)["interactive"] is False
    assert _diagnose_button_state("   ", None, None)["interactive"] is False
    assert _diagnose_button_state("brown spots", None, None)["interactive"] is True
    assert _diagnose_button_state(None, "/tmp/voice.wav", None)["interactive"] is True
    assert _diagnose_button_state(None, None, "/tmp/crop.jpg")["interactive"] is True


def test_swahili_response_uses_localized_message_and_labels() -> None:
    result = _result().model_copy(
        update={
            "language": "sw",
            "localized_condition": "Madoa ya majani yanayowezekana",
            "localized_message": "Ondoa majani yaliyoathirika.",
        }
    )

    from frontend.app_ui import _render_response

    response = _render_response(result)
    assert "### Madoa ya majani yanayowezekana / Possible leaf spot" in response
    assert "Ondoa majani yaliyoathirika." in response
    assert "**Wastani** | Uhakika: **72%**" in response
    assert "Hakuna wauzaji waliopendekezwa" in response
    assert "Moderate" not in response
    assert "Confidence" not in response
    assert "Nearby agro-dealers" not in response


def test_swahili_low_confidence_does_not_show_english_placeholder_as_disease() -> None:
    result = _result().model_copy(
        update={
            "language": "sw",
            "diagnosis": _result().diagnosis.model_copy(
                update={"condition": "Needs review", "confidence": 0.1}
            ),
            "localized_message": "Tatizo halijathibitishwa.",
            "low_confidence": True,
        }
    )

    response = _render_response(result)

    assert " / Needs review" not in response
    assert "Needs review" not in response
    assert "Tatizo halijathibitishwa." in response


def test_dynamic_agrovet_result_includes_distance_phone_and_map() -> None:
    result = _result().model_copy(
        update={
            "dealer_search_status": "success",
            "dealer_search_radius_km": 10,
            "dealers": [
                Dealer(
                    name="Kisumu Agrovet",
                    address="Kisumu, Kenya",
                    rating=4.6,
                    phone="+254 700 000 000",
                    lat=-0.1,
                    lon=34.7,
                    distance_km=2.3,
                    maps_link="https://maps.google.com/example",
                )
            ],
        }
    )

    response = _render_response(result)
    assert "Kisumu Agrovet" in response
    assert "2.3 km" in response
    assert "+254 700 000 000" in response
    assert "[Open map](https://maps.google.com/example)" in response


def test_agrovet_results_show_nearest_five_per_page() -> None:
    result = _result().model_copy(
        update={"dealer_search_status": "success", "dealers": _dealers(7)}
    )

    first_page = _render_response(result)
    second_page, page, pager, previous, next_button, label = _next_dealer_page(
        result, 0
    )

    assert all(f"Agrovet {index}" in first_page for index in range(1, 6))
    assert "Agrovet 6" not in first_page
    assert "Agrovet 1" not in second_page
    assert "Agrovet 6" in second_page
    assert "Agrovet 7" in second_page
    assert page == 1
    assert pager["visible"] is True
    assert previous["interactive"] is True
    assert next_button["interactive"] is False
    assert label == "Page 2 of 2"


def test_five_agrovets_do_not_show_pagination() -> None:
    result = _result().model_copy(
        update={"dealer_search_status": "success", "dealers": _dealers(5)}
    )

    page, pager, previous, next_button, label = _dealer_pagination_updates(result)

    assert page == 0
    assert pager["visible"] is False
    assert previous["interactive"] is False
    assert next_button["interactive"] is False
    assert label == ""
