"""One-screen Gradio Blocks UI wired to the orchestration pipeline."""

from __future__ import annotations

from typing import Optional

import gradio as gr

from backend.core.models import AnalyzeRequest, AnalyzeResult, Severity
from backend.core.orchestration import analyze
from frontend.strings import LANGUAGE_CHOICES, UI

_SEVERITY_EMOJI = {
    Severity.MILD: "🟢",
    Severity.MODERATE: "🟡",
    Severity.SEVERE: "🔴",
    Severity.UNKNOWN: "⚪",
}


def _render_diagnosis(result: AnalyzeResult) -> str:
    """Format the diagnosis as a compact Markdown card."""

    d = result.diagnosis
    emoji = _SEVERITY_EMOJI.get(d.severity, "⚪")
    lines = [
        f"### {emoji} {d.condition}",
        f"**Severity:** {d.severity.value}  ·  **Confidence:** {d.confidence:.0%}",
        "",
        result.localized_message,
    ]
    if d.escalate:
        lines.append("\n> ⚠️ **Please consult a vet or extension officer.**")
    if result.low_confidence:
        lines.append("\n> ℹ️ Low confidence — please send a clearer photo or more detail.")
    return "\n".join(lines)


def _render_dealers(result: AnalyzeResult) -> str:
    """Format the dealer list as Markdown, or a gentle empty-state."""

    if not result.dealers:
        return "_No dealer suggestions for this result._"
    rows = ["| Dealer | Town | Phone | Specialties |", "|---|---|---|---|"]
    for d in result.dealers:
        dist = f" ({d.distance_km} km)" if d.distance_km is not None else ""
        rows.append(f"| {d.name}{dist} | {d.town} | {d.phone} | {d.specialties} |")
    return "\n".join(rows)


def _on_submit(
    language: str,
    audio_path: Optional[str],
    image_path: Optional[str],
    text: Optional[str],
    county: Optional[str],
):
    """Gradio callback: build the request, run the pipeline, render outputs."""

    req = AnalyzeRequest(
        language=language,
        audio_path=audio_path,
        image_path=image_path,
        text=text,
        county=county or None,
    )
    result = analyze(req)
    transcript = result.transcript or "_(no voice/text provided)_"
    return (
        transcript,
        _render_diagnosis(result),
        result.audio_reply_path,
        _render_dealers(result),
    )


def build_ui() -> gr.Blocks:
    """Construct the Gradio Blocks app."""

    with gr.Blocks(title="AfriFarmAI") as demo:
        gr.Markdown(f"# {UI['title']}\n{UI['subtitle']}")

        with gr.Row():
            with gr.Column(scale=1):
                language = gr.Dropdown(
                    choices=LANGUAGE_CHOICES, value="sw", label=UI["language"]
                )
                audio = gr.Audio(
                    sources=["microphone", "upload"], type="filepath", label=UI["voice"]
                )
                image = gr.Image(type="filepath", label=UI["image"])
                text = gr.Textbox(lines=2, label=UI["text"], placeholder="…")
                county = gr.Textbox(label=UI["county"], placeholder="e.g. Kisumu")
                submit = gr.Button(UI["submit"], variant="primary")

            with gr.Column(scale=2):
                transcript_out = gr.Markdown(label=UI["transcript"])
                diagnosis_out = gr.Markdown(label=UI["diagnosis"])
                audio_out = gr.Audio(label=UI["reply_audio"], autoplay=False)
                dealers_out = gr.Markdown(label=UI["dealers"])

        gr.Markdown(f"---\n_{UI['disclaimer']}_")

        submit.click(
            _on_submit,
            inputs=[language, audio, image, text, county],
            outputs=[transcript_out, diagnosis_out, audio_out, dealers_out],
        )

    return demo
