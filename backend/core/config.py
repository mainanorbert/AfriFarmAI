"""Read-once application configuration loaded from environment.

Values are read a single time at import so provider clients and the
orchestration layer share one consistent view. Keep this module free of
secrets in source — everything comes from the environment / `.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)  # no-op if .env is absent (e.g. on Hugging Face Spaces)


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings for AfriFarmAI.

    The app always calls the real providers; missing keys surface as runtime
    errors to the user rather than falling back to canned data.
    """

    hf_token: str = os.getenv("HF_TOKEN", "")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    google_places_api_key: str = os.getenv("GOOGLE_PLACES_API_KEY", "")
    modal_tts_url: str = os.getenv("MODAL_TTS_URL", "")
    modal_key: str = os.getenv("MODAL_KEY", "")
    modal_secret: str = os.getenv("MODAL_SECRET", "")

    nvidia_model_name: str = os.getenv(
        "NVIDIA_MODEL_NAME",
        os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"),
    )
    nvidia_base_url: str = os.getenv(
        "NVIDIA_BASE_URL",
        os.getenv("NEMOTRON_BASE_URL", "https://integrate.api.nvidia.com/v1"),
    )
    tiny_aya_model: str = os.getenv("TINY_AYA_MODEL", "CohereLabs/tiny-aya-global")
    asr_model: str = os.getenv("ASR_MODEL", "openai/whisper-large-v3")
    cohere_transcribe_model: str = os.getenv(
        "COHERE_TRANSCRIBE_MODEL", "cohere-transcribe-03-2026"
    )

    provider_timeout_seconds: int = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "30"))
    modal_tts_timeout_seconds: int = int(os.getenv("MODAL_TTS_TIMEOUT_SECONDS", "300"))
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", "0.45"))

    @property
    def nemotron_model(self) -> str:
        """Compatibility alias used by the diagnosis provider."""

        return self.nvidia_model_name

    @property
    def nemotron_base_url(self) -> str:
        """Compatibility alias used by the diagnosis provider."""

        return self.nvidia_base_url


def get_settings() -> Settings:
    """Load and validate the required NVIDIA chat settings from ``ENV_FILE``."""

    values = dotenv_values(ENV_FILE)
    required = ["NVIDIA_API_KEY", "NVIDIA_MODEL_NAME", "NVIDIA_BASE_URL"]
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise RuntimeError(f"Missing required settings: {', '.join(missing)}")

    return Settings(
        nvidia_api_key=str(values["NVIDIA_API_KEY"]),
        nvidia_model_name=str(values["NVIDIA_MODEL_NAME"]),
        nvidia_base_url=str(values["NVIDIA_BASE_URL"]).rstrip("/"),
    )


settings = Settings()
