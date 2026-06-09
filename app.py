"""AfriFarmAI entry point. Hugging Face Spaces runs this file by default."""

from __future__ import annotations

import gradio as gr

from frontend.app_ui import build_ui

demo = build_ui()

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
