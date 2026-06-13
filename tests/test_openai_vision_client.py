"""GPT-5.4 image-diagnosis fallback behavior without network calls."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APIConnectionError

from backend.core.errors import ProviderError
from backend.services import openai_vision_client as vision


def _response():
    return SimpleNamespace(
        output_text=json.dumps(
            {
                "subject": "crop",
                "condition": "Maize leaf blight",
                "severity": "moderate",
                "confidence": 0.82,
                "treatment": "Remove badly affected leaves and seek local advice.",
                "prevention": "Rotate crops and use clean seed.",
                "escalate": False,
            }
        )
    )


def test_diagnose_sends_original_detail_image_and_structured_output(
    monkeypatch, tmp_path
):
    image = tmp_path / "leaf.jpg"
    image.write_bytes(b"image")
    create = Mock(return_value=_response())
    monkeypatch.setattr(
        vision,
        "OpenAI",
        lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)),
    )

    diagnosis = vision.diagnose("brown maize leaf spots", str(image))

    assert diagnosis.condition == "Maize leaf blight"
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "gpt-5.4"
    assert kwargs["input"][0]["content"][1]["detail"] == "original"
    assert kwargs["text"]["format"]["type"] == "json_schema"
    assert kwargs["store"] is False


def test_diagnose_rejects_unsupported_image_type(tmp_path):
    image = tmp_path / "leaf.bmp"
    image.write_bytes(b"image")

    with pytest.raises(ProviderError, match="OpenAI vision fallback failed"):
        vision.diagnose("", str(image))


def test_diagnose_wraps_openai_failure(monkeypatch, tmp_path):
    image = tmp_path / "leaf.png"
    image.write_bytes(b"image")
    create = Mock(side_effect=APIConnectionError(request=Mock()))
    monkeypatch.setattr(
        vision,
        "OpenAI",
        lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)),
    )

    with pytest.raises(ProviderError, match="OpenAI vision fallback failed"):
        vision.diagnose("", str(image))
