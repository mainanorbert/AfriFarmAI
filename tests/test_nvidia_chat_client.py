from types import SimpleNamespace
from unittest.mock import Mock

from backend.core.config import Settings
from backend.services.nvidia_chat_client import NvidiaChatClient


def test_chat_returns_model_answer() -> None:
    client = NvidiaChatClient(
        Settings(
            nvidia_api_key="test-key",
            nvidia_model_name="test-model",
            nvidia_base_url="https://nvidia.test/v1",
        )
    )
    create = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Model answer"))]
        )
    )
    client._client.chat.completions.create = create

    assert client.chat("Hello") == "Model answer"
    assert create.call_args.kwargs["model"] == "test-model"
    assert create.call_args.kwargs["messages"] == [{"role": "user", "content": "Hello"}]
