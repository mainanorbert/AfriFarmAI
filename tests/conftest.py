"""Force deterministic, offline stub mode for the whole test suite.

Set before any backend module (and its read-once ``settings``) is imported, so
a developer's ``.env`` with ``USE_REAL_MODELS=true`` never sends tests to the
live providers. ``load_dotenv`` does not override already-set env vars.
"""

import os

for _var in (
    "USE_REAL_MODELS",
    "USE_REAL_NEMOTRON",
    "USE_REAL_STT",
    "USE_REAL_AYA",
    "USE_REAL_TTS",
):
    os.environ[_var] = "false"
