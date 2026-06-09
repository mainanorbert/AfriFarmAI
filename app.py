"""AfriFarmAI entry point. Hugging Face Spaces runs this file by default."""

from __future__ import annotations

from frontend.app_ui import APP_CSS, build_ui

demo = build_ui()

if __name__ == "__main__":
    demo.launch(css=APP_CSS)
