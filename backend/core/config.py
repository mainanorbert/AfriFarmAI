"""Read-once application configuration loaded from environment.

Values are read a single time at import so provider clients and the
orchestration layer share one consistent view. Keep this module free of
secrets in source — everything comes from the environment / `.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # no-op if .env is absent (e.g. on Hugging Face Spaces secrets)


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings for AfriFarmAI."""

    use_real_models: bool = _flag("USE_REAL_MODELS", False)

    hf_token: str = os.getenv("HF_TOKEN", "")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")

    nemotron_model: str = os.getenv(
        "NEMOTRON_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    )
    tiny_aya_model: str = os.getenv("TINY_AYA_MODEL", "CohereLabs/tiny-aya-global")
    asr_model: str = os.getenv("ASR_MODEL", "openai/whisper-large-v3")

    provider_timeout_seconds: int = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "30"))
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", "0.45"))


settings = Settings()
