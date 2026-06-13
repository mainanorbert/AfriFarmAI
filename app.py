"""AfriFarmAI entry point. Hugging Face Spaces runs this file by default."""

from __future__ import annotations

import warnings

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from starlette.exceptions import StarletteDeprecationWarning

# Gradio 6.17.3 currently uses Starlette's renamed HTTP 422 constant. This is
# harmless framework noise and does not represent a failed farmer request.
warnings.filterwarnings(
    "ignore",
    message="'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated.*",
    category=StarletteDeprecationWarning,
    module=r"gradio\.routes",
)

from frontend.app_ui import APP_CSS, THEME, build_ui

log = get_logger("app")
log.info(
    "startup op=provider_config nvidia=%s openai=%s openai_host=%s "
    "cohere=%s hf=%s google=%s",
    bool(settings.nvidia_api_key),
    bool(settings.openai_api_key),
    settings.openai_base_host,
    bool(settings.cohere_api_key),
    bool(settings.hf_token),
    bool(settings.google_places_api_key),
)

demo = build_ui()

if __name__ == "__main__":
    demo.launch(css=APP_CSS, theme=THEME)
