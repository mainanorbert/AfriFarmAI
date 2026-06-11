"""AfriFarmAI entry point. Hugging Face Spaces runs this file by default."""

from __future__ import annotations

from frontend.app_ui import APP_CSS, THEME, build_ui

demo = build_ui()

if __name__ == "__main__":
    demo.launch(css=APP_CSS, theme=THEME, share=True)
