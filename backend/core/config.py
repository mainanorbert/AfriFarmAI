from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str
    nvidia_model_name: str
    nvidia_base_url: str


def get_settings() -> Settings:
    """Read and validate the NVIDIA API configuration from the root .env file."""
    values = dotenv_values(ENV_FILE)
    api_key = (values.get("NVIDIA_API_KEY") or "").strip()
    model_name = (values.get("NVIDIA_MODEL_NAME") or "").strip()
    base_url = (values.get("NVIDIA_BASE_URL") or "").strip().rstrip("/")

    missing = [
        name
        for name, value in (
            ("NVIDIA_API_KEY", api_key),
            ("NVIDIA_MODEL_NAME", model_name),
            ("NVIDIA_BASE_URL", base_url),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variable(s): {', '.join(missing)}")

    return Settings(
        nvidia_api_key=api_key,
        nvidia_model_name=model_name,
        nvidia_base_url=base_url,
    )
