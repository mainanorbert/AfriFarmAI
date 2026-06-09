"""Centered Gradio chat interface wired to the orchestration pipeline."""

from __future__ import annotations

from typing import Optional

import gradio as gr

from backend.core.models import AnalyzeRequest, AnalyzeResult, Severity
from backend.core.orchestration import analyze
from frontend.strings import LANGUAGE_CHOICES, UI

APP_CSS = """
.gradio-container {
    background:
        radial-gradient(circle at 15% 0%, rgba(214, 244, 220, .75), transparent 32rem),
        linear-gradient(180deg, #fbfdf9 0%, #f4f8f1 100%);
}
.app-shell { max-width: 900px; margin: 0 auto; }
.top-tools {
    position: fixed !important;
    top: 16px;
    right: 22px;
    z-index: 20;
    width: auto !important;
    min-width: 0 !important;
    padding: 0;
    gap: 6px !important;
}
.theme-toggle {
    flex: 0 0 34px !important;
    min-width: 34px !important;
    width: 34px !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    font-size: 1rem !important;
}
.brand-copy h1 {
    margin-bottom: .15rem;
    color: #173f2a;
    font-size: clamp(1.65rem, 4vw, 2.35rem);
}
.brand-copy p { margin: 0; color: #587061; }
.language-picker {
    flex: 0 0 165px !important;
    width: 165px !important;
    min-width: 165px !important;
    min-height: 32px !important;
    height: 32px !important;
    max-height: 32px !important;
    align-self: flex-start;
    margin-left: auto;
    overflow: visible !important;
}
.language-picker > div,
.language-picker input {
    min-height: 32px !important;
    height: 32px !important;
    max-height: 32px !important;
}
.language-picker input {
    padding: 4px 30px 4px 9px !important;
    font-size: .82rem !important;
}
.response-card {
    margin-top: 8px;
    padding: 18px !important;
    border: 1px solid #dce9dc !important;
    border-radius: 22px !important;
    box-shadow: 0 16px 44px rgba(32, 74, 48, .08);
    background: rgba(255, 255, 255, .88) !important;
}
.response-card .prose {
    max-width: none !important;
}
.response-audio {
    margin-top: 12px;
    border-top: 1px solid #e4ece4;
    padding-top: 12px;
}
.composer {
    margin-top: 12px;
    padding: 12px !important;
    border: 1px solid #262626 !important;
    border-radius: 20px !important;
    background: #111111 !important;
    box-shadow: 0 12px 34px rgba(32, 74, 48, .10);
}
.composer > div,
.prompt-row,
.prompt-row > div {
    background-color: #111111 !important;
}
.composer-text textarea {
    min-height: 72px !important;
    border: 0 !important;
    box-shadow: none !important;
    font-size: 1rem !important;
    color: #f8fafc !important;
    background-color: #111111 !important;
}
.composer-text textarea::placeholder {
    color: #9ca3af !important;
}
.composer-action {
    flex: 0 0 142px !important;
    min-width: 142px !important;
    max-width: 142px !important;
    padding-inline: 10px !important;
}
.prompt-row { align-items: stretch !important; }
.prompt-row .composer-action {
    align-self: stretch;
    min-height: 72px !important;
}
.record-control {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 58px !important;
    margin-top: 8px;
    padding: 6px !important;
    border-color: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}
.record-control button {
    color: #dc2626 !important;
    background-color: transparent !important;
}
.photo-upload {
    flex: 0 0 50px !important;
    min-width: 50px !important;
    max-width: 50px !important;
    align-self: stretch;
}
.photo-upload,
.photo-upload button {
    min-width: 50px !important;
    min-height: 72px !important;
    padding: 8px !important;
    color: transparent !important;
    font-size: 0 !important;
    background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJ8AAACUCAMAAAC6AgsRAAAAYFBMVEX///8AAADp6eng4OANDQ2qqqpRUVGamppKSkrU1NSkpKSIiIjNzc1CQkInJyf7+/v19fVkZGRfX1/FxcXa2tpqamo4ODh3d3e4uLh+fn4xMTEVFRWQkJBXV1e/v78dHR1euqxzAAAEaklEQVR4nO2a6ZKzKhBAFeOeBOKu0fj+b3lVXBG/qKGTqbp9fk05Mp4BGppF0xAEQRAEQRAEQRAEQRAEQZD/L8QwCP21xBbMzB+WFaT2y/i1igwzueicOnH8F/u1zxL20AWecWawv2JJAlGvI8nNMPoDjjSX6nU4aWlGPw6a67ZeyyWpUvOXQVP3geEREua3+1NuGXgR+0lFRlzg0fc08ipj6y6vyocXRuTbfiXvaLMWpCQ0fXnM6EVcmtevBg0X8YWnlERh6cgdkyou3W+1Nbm1n3xmst9Rei2t+iJzfNZO6X6jHsOurxXb3Yq6dlwl8ppMr+B+Hm+yf79ErmYZSx1t6HjxeUW8f7HpkN5jPfjEsIKET73S7reGMterxDYG7YUuH+oOVUJkplUy1aQN5dby4t84XC7K7HQYxSFb2N7b/dawa5+WiWOnMogZ8Dq4O7up/LApyUfnvvMWMHbuxvTwHnMICT541hGAHTPP2jXE/WzNumB+vgD07A/0dN3qY6KbvC87R6cjZB/p6XrA/0uo+jPq4UOXgwzlulHP7ea8Wn12zWc1/Z575kHKfv6wWimz0wWIX/6N25mGIf1yqu10PLetVNtpRvd3m6SPaoZnH6D9hyif2kqqsXRqaqXw6IjZMH/sx2kC1xxKR11uq6sf/njS18xL4UG9Ziqkmtv9EJChtPpUf/SLD/vdosmPV6SlXG/yuw2frSUqUu7XwY9RqO638ksJY+7Gonfbj/ESAGsQwc/rHtJd+cLMj/AHAHsfS7+gn0yv0pXkth8fBR4A6enSb8gvibi0eOPHu18JsFJf+pWD355onvwo736mej3BL++fGrcNp+csdEa/B+9+BcQSfemXuPOna9LsZY/jz+gX8+5XQayOhPgNuhDMNgaYvO1gY744+qW8+51aWh300xM/M+ONIbrfGBwm6ql9ednyzaeU+P2Dof36aJ38+EbrM/yt321MToxk6dfrgizO9/u5U6FQ5udA6G34SaaP2cqM8mxZ8Mu3P6LYr2ha8iWEsLco1R0zCX4wG5Rrv8TupinDmuuJU1eUrPxgNtdWfvkQBmR2mLTe2csugt8dRE/0S7LJZNr3SCR14wt+IKOz4Hfx5yJ0OO96SkeOe73wA9jZEPwu1mr5ZbR51l2+KiPFwg/oXG70KwpP0orET6pQk+d12dzPAdo6Hf1KeQWw7WM2ymZ+OdDe+Oh3Kved/Lz3L59CkR/ExmTH6HeK0c+B2NhtUeQXQx3NKPKDSQ40VX4Q+84cNX4bQ7gC1Pi9OZT9ADV+D6VOc9T4QewccNT4wV3aUeOnVGmBEj/1xwojSvygkgNtOCE4e3Og34tx3795Fl4DZ7fG+BovgTzW73vQqU/023AQ+6Yj/c2BOjPIQYZLBwlg846X6j6gPJnc7oOWH+rdgO81ra/sHgO0dTvBjQuI+4C/t9bE4calubcU6XcueRKvvdN+kCD1wdt2pmgchfyBG9sIgiAIgiAIgiAIgiAIgiDId/gPbr86JgahX/sAAAAASUVORK5CYII=") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 31px 29px !important;
    background-color: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}
.photo-upload:hover,
.photo-upload button:hover,
.record-control:hover {
    background-color: #262626 !important;
}
.image-preview {
    width: 120px !important;
    max-width: 120px !important;
    margin-top: 8px;
}
.image-preview img {
    object-fit: cover !important;
    border-radius: 12px !important;
}
.secondary-details { margin-top: 10px; }
.disclaimer {
    color: #718078;
    font-size: .82rem;
    text-align: center;
    padding: 14px 20px 4px;
}
.dark-mode .gradio-container {
    color: #e5e7eb !important;
    background:
        radial-gradient(circle at 15% 0%, rgba(31, 74, 50, .55), transparent 32rem),
        linear-gradient(180deg, #0b100d 0%, #111713 100%) !important;
}
.dark-mode .brand-copy h1 { color: #d8f3df !important; }
.dark-mode .brand-copy p,
.dark-mode .disclaimer { color: #a5b5aa !important; }
.dark-mode .response-card,
.dark-mode .record-control,
.dark-mode .secondary-details,
.dark-mode .secondary-details > div {
    color: #e5e7eb !important;
    border-color: #37463b !important;
    background-color: #161d18 !important;
}
.dark-mode .response-card table,
.dark-mode .response-card th,
.dark-mode .response-card td {
    color: #e5e7eb !important;
    border-color: #45574a !important;
}
.dark-mode .language-picker input,
.dark-mode .language-picker > div,
.dark-mode .theme-toggle {
    color: #e5e7eb !important;
    border-color: #45574a !important;
    background-color: #161d18 !important;
}
.dark-mode .response-audio { border-color: #37463b !important; }
@media (max-width: 680px) {
    .gradio-container {
        padding-inline: 8px !important;
    }
    .app-shell {
        width: 100% !important;
        padding-top: 42px;
    }
    .top-tools {
        top: 10px;
        right: 10px;
    }
    .language-picker {
        flex-basis: 140px !important;
        width: 140px !important;
        min-width: 140px !important;
    }
    .brand-copy h1 {
        font-size: 1.55rem;
    }
    .brand-copy p {
        font-size: .88rem;
    }
    .composer {
        padding: 8px !important;
        border-radius: 16px !important;
    }
    .prompt-row {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
    }
    .composer-text {
        order: 1;
        flex: 1 0 100% !important;
        width: 100% !important;
        min-width: 0 !important;
    }
    .composer-text textarea {
        min-height: 88px !important;
        padding: 10px !important;
    }
    .photo-upload {
        order: 2;
        flex: 0 0 48px !important;
        min-width: 48px !important;
        max-width: 48px !important;
    }
    .photo-upload,
    .photo-upload button {
        min-width: 48px !important;
        min-height: 48px !important;
        height: 48px !important;
        background-size: 26px 24px !important;
    }
    .composer-action {
        order: 4;
        flex: 0 0 124px !important;
        min-width: 124px !important;
        max-width: 124px !important;
        min-height: 48px !important;
        height: 48px !important;
        padding-inline: 8px !important;
    }
    .record-control {
        width: 100% !important;
        min-width: 0 !important;
        min-height: 48px !important;
        margin-top: 6px;
    }
    .prompt-row .composer-action {
        min-height: 48px !important;
    }
    .image-preview {
        width: 96px !important;
        max-width: 96px !important;
    }
}
"""

_SEVERITY_MARKERS = {
    Severity.MILD: "Mild",
    Severity.MODERATE: "Moderate",
    Severity.SEVERE: "Severe",
    Severity.UNKNOWN: "Needs review",
}

_RESPONSE_LABELS = {
    "sw": {
        "description": "Maelezo yako",
        "dealers": "Wauzaji wa pembejeo walio karibu",
        "no_dealers": "Hakuna wauzaji waliopendekezwa kwa jibu hili.",
        "escalate": "Tafadhali wasiliana na daktari wa mifugo au afisa wa ugani.",
        "low_confidence": "Uhakika ni mdogo: tafadhali tuma picha iliyo wazi au maelezo zaidi.",
    },
    "luo": {
        "description": "Wach mari",
        "dealers": "Jo-usumb gik pur machiegni",
        "no_dealers": "Onge ja-usumb ma oyier ne dwoko ni.",
        "escalate": "Tim ber iwuoyo gi jadaktar mar jamni kata jatich mar pur.",
        "low_confidence": "Genruok en matin: tim ber ior picha maler kata wach mang'eny.",
    },
    "en": {
        "description": "Your description",
        "dealers": "Nearby agro-dealers",
        "no_dealers": "No dealer suggestions for this result.",
        "escalate": "Please consult a vet or extension officer.",
        "low_confidence": "Low confidence: please send a clearer photo or more detail.",
    },
}

_GEO_JS = """
() => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve([null, null, "Geolocation not supported on this device"]);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => resolve([p.coords.latitude, p.coords.longitude,
                      "Location set (" + p.coords.latitude.toFixed(3) + ", "
                      + p.coords.longitude.toFixed(3) + ")"]),
      () => resolve([null, null, "Location unavailable or permission denied"]),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}
"""

_THEME_JS = """
() => {
  const root = document.documentElement;
  const dark = !root.classList.contains("dark-mode");
  root.classList.toggle("dark-mode", dark);
  localStorage.setItem("afrifarm-theme", dark ? "dark" : "light");
  return dark ? "\u2600" : "\u263E";
}
"""

_THEME_INIT_JS = """
() => {
  const dark = localStorage.getItem("afrifarm-theme") === "dark";
  document.documentElement.classList.toggle("dark-mode", dark);
}
"""

def _render_diagnosis(result: AnalyzeResult) -> str:
    """Format a diagnosis for an assistant chat message."""

    diagnosis = result.diagnosis
    labels = _RESPONSE_LABELS[result.language]
    if result.language != "en":
        lines = [result.localized_message]
        if diagnosis.escalate:
            lines.append(f"\n> {labels['escalate']}")
        if result.low_confidence:
            lines.append(f"\n> {labels['low_confidence']}")
        return "\n".join(lines)

    marker = _SEVERITY_MARKERS.get(diagnosis.severity, "Needs review")
    lines = [
        f"### {diagnosis.condition}",
        f"**{marker}** | Confidence: **{diagnosis.confidence:.0%}**",
        "",
        result.localized_message,
    ]
    if diagnosis.escalate:
        lines.append("\n> Please consult a vet or extension officer.")
    if result.low_confidence:
        lines.append("\n> Low confidence: please send a clearer photo or more detail.")
    return "\n".join(lines)


def _render_dealers(result: AnalyzeResult) -> str:
    """Format the dealer list as Markdown, or a gentle empty-state."""

    if not result.dealers:
        return f"_{_RESPONSE_LABELS[result.language]['no_dealers']}_"
    rows = ["| Dealer | Town | Phone | Specialties |", "|---|---|---|---|"]
    for dealer in result.dealers:
        distance = (
            f" ({dealer.distance_km} km)" if dealer.distance_km is not None else ""
        )
        rows.append(
            f"| {dealer.name}{distance} | {dealer.town} | "
            f"{dealer.phone} | {dealer.specialties} |"
        )
    return "\n".join(rows)


def _render_response(result: AnalyzeResult) -> str:
    """Combine the diagnosis and dealer guidance into one response."""

    labels = _RESPONSE_LABELS[result.language]
    transcript = result.transcript or "_Photo or voice message submitted._"
    return "\n\n".join(
        [
            f"**{labels['description']}:** {transcript}",
            _render_diagnosis(result),
            f"### {labels['dealers']}\n{_render_dealers(result)}",
        ]
    )


def _on_submit(
    language: str,
    audio_path: Optional[str],
    image_path: Optional[str],
    text: Optional[str],
    county: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
):
    """Run the pipeline and return one unified response."""

    request = AnalyzeRequest(
        language=language,
        audio_path=audio_path,
        image_path=image_path,
        text=text,
        county=county or None,
        lat=lat,
        lon=lon,
    )
    result = analyze(request)
    return (
        _render_response(result),
        result.audio_reply_path,
        "",
        None,
        None,
    )


def build_ui() -> gr.Blocks:
    """Construct the centered chat interface."""

    with gr.Blocks(title="AfriFarmAI") as demo:
        with gr.Row(elem_classes=["top-tools"]):
            theme = gr.Button(
                "\u263E",
                size="sm",
                min_width=34,
                elem_classes=["theme-toggle"],
            )
            language = gr.Dropdown(
                choices=LANGUAGE_CHOICES,
                value="sw",
                label=UI["language"],
                show_label=False,
                container=False,
                elem_classes=["language-picker"],
            )
        demo.load(fn=None, js=_THEME_INIT_JS)

        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                f"<div class='brand-copy'><h1>{UI['title']}</h1>"
                f"<p>{UI['subtitle']}</p></div>"
            )

            with gr.Group(visible=False, elem_classes=["response-card"]) as response_card:
                response_text = gr.Markdown(
                    value="",
                    label=None,
                    show_label=False,
                )
                audio_out = gr.Audio(
                    label=UI["reply_audio"],
                    autoplay=False,
                    elem_classes=["response-audio"],
                )

            with gr.Group(elem_classes=["composer"]):
                with gr.Row(equal_height=True, elem_classes=["prompt-row"]):
                    image = gr.UploadButton(
                        UI["photo_icon"],
                        file_types=["image"],
                        type="filepath",
                        scale=0,
                        min_width=50,
                        elem_classes=["photo-upload"],
                    )
                    text = gr.Textbox(
                        lines=2,
                        max_lines=5,
                        show_label=False,
                        container=False,
                        placeholder=UI["prompt_placeholder"],
                        scale=8,
                        elem_classes=["composer-text"],
                    )
                    submit = gr.Button(
                        UI["submit"],
                        variant="primary",
                        scale=0,
                        min_width=142,
                        elem_classes=["composer-action"],
                    )
                image_preview = gr.Image(
                    type="filepath",
                    show_label=False,
                    container=False,
                    interactive=False,
                    visible=False,
                    height=105,
                    width=120,
                    buttons=[],
                    elem_classes=["image-preview"],
                )

            audio = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label=UI["voice"],
                show_label=True,
                container=True,
                recording=False,
                buttons=[],
                elem_classes=["record-control"],
            )

            with gr.Accordion(
                UI["more_options"], open=False, elem_classes=["secondary-details"]
            ):
                county = gr.Textbox(label=UI["county"], placeholder="e.g. Kisumu")
                with gr.Row():
                    locate = gr.Button(UI["use_location"], size="sm")
                    loc_status = gr.Textbox(
                        label=UI["location_status"], interactive=False, scale=2
                    )

            lat = gr.Number(visible=False)
            lon = gr.Number(visible=False)
            gr.HTML(f"<div class='disclaimer'>{UI['disclaimer']}</div>")

        locate.click(fn=None, inputs=None, outputs=[lat, lon, loc_status], js=_GEO_JS)
        theme.click(fn=None, outputs=theme, js=_THEME_JS, queue=False)
        image.upload(
            lambda path: (path, gr.update(visible=True)),
            inputs=image,
            outputs=[image_preview, image_preview],
            show_progress="hidden",
        )
        submit.click(
            _on_submit,
            inputs=[language, audio, image, text, county, lat, lon],
            outputs=[response_text, audio_out, text, audio, image],
        ).then(
            lambda: (
                gr.update(visible=True),
                None,
                gr.update(visible=False),
            ),
            outputs=[response_card, image_preview, image_preview],
        )
        text.submit(
            _on_submit,
            inputs=[language, audio, image, text, county, lat, lon],
            outputs=[response_text, audio_out, text, audio, image],
        ).then(
            lambda: (
                gr.update(visible=True),
                None,
                gr.update(visible=False),
            ),
            outputs=[response_card, image_preview, image_preview],
        )

    return demo
