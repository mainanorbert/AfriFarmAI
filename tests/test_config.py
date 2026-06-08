import pytest

from backend.core import config


def test_get_settings_reads_nvidia_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NVIDIA_API_KEY=test-key\n"
        "NVIDIA_MODEL_NAME=test-model\n"
        "NVIDIA_BASE_URL=https://nvidia.test/v1/\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "ENV_FILE", env_file)

    settings = config.get_settings()

    assert settings.nvidia_api_key == "test-key"
    assert settings.nvidia_model_name == "test-model"
    assert settings.nvidia_base_url == "https://nvidia.test/v1"


def test_get_settings_requires_all_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)

    with pytest.raises(
        RuntimeError,
        match="NVIDIA_API_KEY, NVIDIA_MODEL_NAME, NVIDIA_BASE_URL",
    ):
        config.get_settings()
