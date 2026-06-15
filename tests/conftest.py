"""Test setup: inject dummy provider keys before the read-once ``settings`` is
imported, so the suite never reaches a real API even if a mock is missed.

Tests mock the provider functions themselves (transcribe/diagnose/localize/
synthesize); these dummy keys are just a safety net. ``load_dotenv`` does not
override already-set env vars, so a developer's real ``.env`` is ignored here.
"""

import os

os.environ.setdefault("HF_TOKEN", "test-hf-token")
os.environ.setdefault("NVIDIA_API_KEY", "test-nvidia-key")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "test-google-key")
