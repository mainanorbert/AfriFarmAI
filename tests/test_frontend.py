from unittest.mock import patch

from backend.core.config import Settings
from frontend.app_ui import respond


def test_respond_adds_prompt_and_answer_to_history() -> None:
    with patch(
        "frontend.app_ui.NvidiaChatClient.chat",
        return_value="Model answer",
    ), patch(
        "frontend.app_ui.get_settings",
        return_value=Settings(
            nvidia_api_key="test-key",
            nvidia_model_name="test-model",
            nvidia_base_url="https://nvidia.test/v1",
        ),
    ):
        cleared, history = respond("Hello", None)

    assert cleared == ""
    assert history == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Model answer"},
    ]


def test_respond_ignores_empty_prompt() -> None:
    assert respond("   ", None) == ("", [])
