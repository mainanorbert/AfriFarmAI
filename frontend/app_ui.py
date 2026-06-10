"""Centered Gradio chat interface wired to the orchestration pipeline."""

from __future__ import annotations

from typing import Optional

import gradio as gr

from backend.core.models import AnalyzeRequest, AnalyzeResult, Severity
from backend.core.orchestration import analyze
from frontend.strings import LANGUAGE_CHOICES, UI

APP_CSS = """
.gradio-container {
    color: #123d25 !important;
    background:
        radial-gradient(circle at 15% 0%, rgba(174, 224, 185, .82), transparent 32rem),
        linear-gradient(180deg, #eff9f0 0%, #dcefdc 100%);
}
.app-shell { max-width: 900px; margin: 0 auto; }
.top-tools {
    position: fixed !important;
    top: 16px;
    right: 22px;
    z-index: 20;
    align-items: center !important;
    flex-wrap: nowrap !important;
    width: auto !important;
    min-width: 0 !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0;
    gap: 6px !important;
}
.theme-toggle,
.location-toggle {
    flex: 0 0 34px !important;
    min-width: 34px !important;
    width: 34px !important;
    height: 32px !important;
    min-height: 32px !important;
    max-height: 32px !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 1rem !important;
    color: #14532d !important;
    border-color: #86b98f !important;
    background: #d9f0dd !important;
}
.location-toggle {
    font-size: 1.15rem !important;
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
    align-self: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
}
.language-picker > div,
.language-picker .wrap,
.language-picker .secondary-wrap,
.language-picker [role="combobox"],
.language-picker input {
    min-height: 32px !important;
    height: 32px !important;
    max-height: 32px !important;
    margin: 0 !important;
    padding-block: 0 !important;
}
.language-picker .wrap,
.language-picker .secondary-wrap {
    align-items: center !important;
}
.language-picker,
.language-picker > div,
.language-picker .wrap,
.language-picker .secondary-wrap {
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.language-picker input {
    padding-inline: 9px 30px !important;
    font-size: .82rem !important;
    line-height: 32px !important;
    color: #174b2b !important;
    border: 1px solid #86b98f !important;
    border-radius: 8px !important;
    background: #e4f4e6 !important;
    box-shadow: none !important;
}
.language-picker button {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.language-picker svg {
    max-height: 24px !important;
}
.response-card {
    margin-top: 8px;
    padding: 18px !important;
    border: 1px solid #91bd98 !important;
    border-radius: 22px !important;
    box-shadow: 0 16px 44px rgba(32, 74, 48, .08);
    background: rgba(226, 244, 229, .94) !important;
}
.user-card {
    margin: 12px 0 8px auto !important;
    max-width: 72%;
    padding: 12px !important;
    border: 1px solid #2f7745 !important;
    border-radius: 18px !important;
    background: #174b2b !important;
}
.user-card .prose { color: #e5f5e8 !important; }
.user-message-stack {
    gap: 8px !important;
}
.user-message-image {
    width: min(100%, 280px) !important;
    max-width: 280px !important;
}
.user-message-image img {
    object-fit: cover !important;
    border-radius: 12px !important;
}
.response-card .prose {
    max-width: none !important;
}
.response-audio {
    margin-top: 12px;
    border-top: 1px solid #9bc5a2;
    padding-top: 12px;
}
.dealer-pagination {
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    margin-top: 10px;
}
.dealer-pagination button {
    flex: 0 0 auto !important;
    min-width: 92px !important;
}
.dealer-page-label {
    flex: 0 0 auto !important;
    min-width: 92px !important;
    text-align: center;
}
.composer {
    margin-top: 12px;
    padding: 12px !important;
    border: 1px solid #2f7745 !important;
    border-radius: 20px !important;
    background: #174b2b !important;
    box-shadow: 0 12px 34px rgba(32, 74, 48, .10);
}
.composer > div,
.prompt-row,
.prompt-row > div {
    background-color: #174b2b !important;
}
.composer-text textarea {
    min-height: 72px !important;
    border: 0 !important;
    box-shadow: none !important;
    font-size: 1rem !important;
    color: #e5f5e8 !important;
    background-color: #174b2b !important;
}
.composer-text textarea::placeholder {
    color: #a8d5b0 !important;
}
.composer-action {
    flex: 0 0 142px !important;
    min-width: 142px !important;
    max-width: 142px !important;
    padding-inline: 10px !important;
    color: #e8f7eb !important;
    border-color: #4d9b62 !important;
    background: #2f7d48 !important;
}
.composer-action:hover {
    background: #3d9257 !important;
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
    color: #174b2b !important;
    border-color: #86b98f !important;
    background-color: #d9f0dd !important;
    box-shadow: none !important;
}
.record-control button {
    color: #1d6b38 !important;
    background-color: #d9f0dd !important;
}
.record-control > div,
.record-control > div > div,
.record-control [class*="container"],
.record-control [class*="waveform"],
.response-audio > div,
.response-audio > div > div {
    color: #174b2b !important;
    border-color: #91bd98 !important;
    background-color: #e4f4e6 !important;
}
.record-control input[type="range"],
.response-audio input[type="range"] {
    accent-color: #2f7d48 !important;
}
.photo-menu-trigger {
    flex: 0 0 50px !important;
    min-width: 50px !important;
    max-width: 50px !important;
    align-self: stretch;
}
.photo-menu-trigger,
.photo-menu-trigger button {
    min-width: 50px !important;
    min-height: 72px !important;
    padding: 8px !important;
    color: transparent !important;
    font-size: 0 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232f7d48' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='6' width='16' height='14' rx='2'/%3E%3Cpath d='M6 6l1-2h11a2 2 0 0 1 2 2v10'/%3E%3Ccircle cx='8' cy='10' r='1' fill='%232f7d48' stroke='none'/%3E%3Cpath d='m4 17 4-4 3 3 3-4 5 5'/%3E%3C/svg%3E") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 31px 29px !important;
    background-color: #174b2b !important;
    border-color: #2f7745 !important;
    box-shadow: none !important;
}
.photo-menu-trigger:hover,
.photo-menu-trigger button:hover,
.record-control:hover {
    background-color: #286a3e !important;
}
.photo-actions {
    width: auto !important;
    min-width: 0 !important;
    margin: 6px 0 0 0 !important;
    gap: 6px !important;
}
.photo-action {
    flex: 0 0 42px !important;
    width: 42px !important;
    min-width: 42px !important;
    max-width: 42px !important;
    height: 38px !important;
    min-height: 38px !important;
    padding: 0 !important;
    color: transparent !important;
    font-size: 0 !important;
    border: 1px solid #4d9b62 !important;
    border-radius: 10px !important;
    background-color: #24663a !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 22px 22px !important;
    box-shadow: none !important;
}
.photo-upload-action,
.photo-upload-action button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23d9f2de' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V4m0 0L7 9m5-5 5 5'/%3E%3Cpath d='M5 14v5h14v-5'/%3E%3C/svg%3E") !important;
}
.photo-camera-action {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23d9f2de' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 7h4l2-3h4l2 3h4v12H4z'/%3E%3Ccircle cx='12' cy='13' r='4'/%3E%3C/svg%3E") !important;
}
.selected-image {
    width: 120px !important;
    max-width: 120px !important;
    margin-top: 8px;
}
.selected-image img,
.camera-capture img {
    object-fit: cover !important;
    border-radius: 12px !important;
}
.camera-capture { margin-top: 8px; }
.disclaimer {
    color: #4d7758;
    font-size: .82rem;
    text-align: center;
    padding: 14px 20px 4px;
}
.dark-mode .gradio-container {
    color: #d9f2de !important;
    background:
        radial-gradient(circle at 15% 0%, rgba(45, 109, 65, .58), transparent 32rem),
        linear-gradient(180deg, #082713 0%, #0d351b 100%) !important;
}
.dark-mode .brand-copy h1 { color: #d8f3df !important; }
.dark-mode .brand-copy p,
.dark-mode .disclaimer { color: #a8d5b0 !important; }
.dark-mode .response-card,
.dark-mode .user-card,
.dark-mode .record-control {
    color: #d9f2de !important;
    border-color: #3f8052 !important;
    background-color: #123f22 !important;
}
.dark-mode .response-card table,
.dark-mode .response-card th,
.dark-mode .response-card td {
    color: #d9f2de !important;
    border-color: #4d9060 !important;
}
.dark-mode .language-picker input,
.dark-mode .theme-toggle,
.dark-mode .location-toggle {
    color: #d9f2de !important;
    border-color: #4d9060 !important;
    background-color: #123f22 !important;
}
.dark-mode .language-picker,
.dark-mode .language-picker > div,
.dark-mode .language-picker .wrap,
.dark-mode .language-picker .secondary-wrap,
.dark-mode .language-picker button {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.dark-mode .response-audio { border-color: #3f8052 !important; }
.dark-mode .record-control > div,
.dark-mode .record-control > div > div,
.dark-mode .record-control [class*="container"],
.dark-mode .record-control [class*="waveform"],
.dark-mode .record-control button,
.dark-mode .response-audio > div,
.dark-mode .response-audio > div > div {
    color: #d9f2de !important;
    border-color: #3f8052 !important;
    background-color: #174b2b !important;
}
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
    .user-card {
        max-width: 92%;
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

_DEALERS_PER_PAGE = 5

_RESPONSE_LABELS = {
    "sw": {
        "description": "Maelezo yako",
        "dealers": "Wauzaji wa pembejeo walio karibu",
        "no_dealers": "Hakuna wauzaji waliopendekezwa kwa jibu hili.",
        "location_required": "Ruhusu eneo lako au bonyeza alama ya eneo juu ili kupata wauzaji wa karibu.",
        "dealer_error": "Hatukuweza kutafuta wauzaji wa karibu kwa sasa. Jaribu tena baadaye.",
        "searched_radius": "Tumetafuta hadi kilomita {radius}.",
        "escalate": "Tafadhali wasiliana na daktari wa mifugo au afisa wa ugani.",
        "low_confidence": "Uhakika ni mdogo: tafadhali tuma picha iliyo wazi au maelezo zaidi.",
    },
    "luo": {
        "description": "Wach mari",
        "dealers": "Jo-usumb gik pur machiegni",
        "no_dealers": "Onge ja-usumb ma oyier ne dwoko ni.",
        "location_required": "Yie mondo wanwang kama intie kata di alama mar kama malo mondo wayud jo-usumb machiegni.",
        "dealer_error": "Ok wanyal manyo jo-usumb machiegni sani. Tem kendo bang'e.",
        "searched_radius": "Wase manyo nyaka kilomita {radius}.",
        "escalate": "Tim ber iwuoyo gi jadaktar mar jamni kata jatich mar pur.",
        "low_confidence": "Genruok en matin: tim ber ior picha maler kata wach mang'eny.",
    },
    "en": {
        "description": "Your description",
        "dealers": "Nearby agro-dealers",
        "no_dealers": "No dealer suggestions for this result.",
        "location_required": "Allow location access or click the location icon above to find nearby agrovets.",
        "dealer_error": "Nearby agrovet search is unavailable right now. Please try again later.",
        "searched_radius": "Searched up to {radius} km.",
        "escalate": "Please consult a vet or extension officer.",
        "low_confidence": "Low confidence: please send a clearer photo or more detail.",
    },
}

_GEO_JS = """
() => {
    return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve([null, null]);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => resolve([p.coords.latitude, p.coords.longitude]),
      () => resolve([null, null]),
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


def _render_dealers(result: AnalyzeResult, page: int = 0) -> str:
    """Format the dealer list as Markdown, or a gentle empty-state."""

    labels = _RESPONSE_LABELS[result.language]
    if result.dealer_search_status == "location_required":
        return f"_{labels['location_required']}_"
    if result.dealer_search_status == "error":
        return f"_{labels['dealer_error']}_"
    if not result.dealers:
        radius_note = (
            " "
            + labels["searched_radius"].format(
                radius=result.dealer_search_radius_km
            )
            if result.dealer_search_radius_km
            else ""
        )
        return f"_{labels['no_dealers']}{radius_note}_"
    rows = [
        "| Agrovet | Address | Rating | Phone | Distance | Map |",
        "|---|---|---:|---|---:|---|",
    ]
    start = max(page, 0) * _DEALERS_PER_PAGE
    for dealer in result.dealers[start : start + _DEALERS_PER_PAGE]:
        rating = f"{dealer.rating:.1f}" if dealer.rating is not None else "—"
        phone = dealer.phone or "—"
        rows.append(
            f"| {dealer.name} | {dealer.address} | {rating} | {phone} | "
            f"{dealer.distance_km:.1f} km | [Open map]({dealer.maps_link}) |"
        )
    return "\n".join(rows)


def _render_response(result: AnalyzeResult, dealer_page: int = 0) -> str:
    """Combine the diagnosis and dealer guidance into one response."""

    labels = _RESPONSE_LABELS[result.language]
    return "\n\n".join(
        [
            _render_diagnosis(result),
            f"### {labels['dealers']}\n{_render_dealers(result, dealer_page)}",
        ]
    )


def _dealer_pagination_updates(result: AnalyzeResult, page: int = 0):
    """Return normalized page state and Gradio updates for dealer navigation."""

    total_pages = max(
        1,
        (len(result.dealers) + _DEALERS_PER_PAGE - 1) // _DEALERS_PER_PAGE,
    )
    normalized_page = min(max(page, 0), total_pages - 1)
    visible = total_pages > 1
    return (
        normalized_page,
        gr.update(visible=visible),
        gr.update(interactive=normalized_page > 0),
        gr.update(interactive=normalized_page < total_pages - 1),
        f"Page {normalized_page + 1} of {total_pages}" if visible else "",
    )


def _change_dealer_page(
    result: Optional[AnalyzeResult],
    current_page: int,
    step: int,
):
    """Render another page from the existing search result without a new lookup."""

    if result is None:
        return "", 0, gr.update(visible=False), gr.update(), gr.update(), ""
    page, pager, previous, next_button, label = _dealer_pagination_updates(
        result,
        current_page + step,
    )
    return _render_response(result, page), page, pager, previous, next_button, label


def _previous_dealer_page(result: Optional[AnalyzeResult], current_page: int):
    """Render the previous dealer page."""

    return _change_dealer_page(result, current_page, -1)


def _next_dealer_page(result: Optional[AnalyzeResult], current_page: int):
    """Render the next dealer page."""

    return _change_dealer_page(result, current_page, 1)


def _on_submit(
    language: str,
    audio_path: Optional[str],
    image_path: Optional[str],
    text: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
):
    """Run the pipeline and return one unified response."""

    request = AnalyzeRequest(
        language=language,
        audio_path=audio_path,
        image_path=image_path,
        text=text,
        lat=lat,
        lon=lon,
    )
    result = analyze(request)
    page, pager, previous, next_button, page_label = _dealer_pagination_updates(result)
    submitted_text = (
        (text or "").strip()
        or (result.transcript or "").strip()
        or "Photo submitted."
    )
    return (
        _render_response(result),
        result.audio_reply_path,
        submitted_text,
        gr.update(value=image_path, visible=bool(image_path)),
        "",
        None,
        gr.update(value=None, visible=False),
        result,
        page,
        pager,
        previous,
        next_button,
        page_label,
    )


def _diagnose_button_state(text: Optional[str]):
    """Enable diagnosis only when the symptom description contains text."""

    return gr.update(interactive=bool(text and text.strip()))


def _captured_image_state(path: Optional[str]):
    """Preserve a captured photo in the composer preview."""

    return (
        gr.update(value=path, visible=bool(path)),
        gr.update(visible=False),
    )


def _show_analysis_loading():
    """Show an honest loading state while diagnosis and agrovet search run."""

    return (
        gr.update(visible=True),
        "Analyzing the symptoms and searching for nearby agrovets...",
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
            locate = gr.Button(
                "\u2316",
                size="sm",
                min_width=34,
                elem_classes=["location-toggle"],
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

            with gr.Group(visible=False, elem_classes=["user-card"]) as user_card:
                with gr.Column(elem_classes=["user-message-stack"]):
                    user_text = gr.Markdown(value="")
                    user_image = gr.Image(
                        type="filepath",
                        show_label=False,
                        container=False,
                        interactive=False,
                        visible=False,
                        buttons=[],
                        elem_classes=["user-message-image"],
                    )

            with gr.Group(visible=False, elem_classes=["response-card"]) as response_card:
                response_text = gr.Markdown(
                    value="",
                    label=None,
                    show_label=False,
                )
                with gr.Row(
                    visible=False,
                    elem_classes=["dealer-pagination"],
                ) as dealer_pager:
                    previous_dealers = gr.Button("Previous", size="sm")
                    dealer_page_label = gr.Markdown(
                        value="",
                        elem_classes=["dealer-page-label"],
                    )
                    next_dealers = gr.Button("Next", size="sm")
                audio_out = gr.Audio(
                    label=UI["reply_audio"],
                    autoplay=False,
                    elem_classes=["response-audio"],
                )

            with gr.Group(elem_classes=["composer"]):
                with gr.Row(equal_height=True, elem_classes=["prompt-row"]):
                    photo_menu = gr.Button(
                        UI["photo_icon"],
                        scale=0,
                        min_width=50,
                        elem_classes=["photo-menu-trigger"],
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
                        interactive=False,
                        scale=0,
                        min_width=142,
                        elem_classes=["composer-action"],
                    )
                with gr.Row(visible=False, elem_classes=["photo-actions"]) as photo_actions:
                    upload_image = gr.UploadButton(
                        "Upload image",
                        file_types=["image"],
                        type="filepath",
                        size="sm",
                        scale=0,
                        min_width=42,
                        elem_classes=["photo-action", "photo-upload-action"],
                    )
                    camera_button = gr.Button(
                        "Take photo",
                        size="sm",
                        scale=0,
                        min_width=42,
                        elem_classes=["photo-action", "photo-camera-action"],
                    )
                selected_image = gr.Image(
                    type="filepath",
                    show_label=False,
                    container=False,
                    interactive=False,
                    visible=False,
                    buttons=[],
                    elem_classes=["selected-image"],
                )
                camera_capture = gr.Image(
                    sources=["webcam"],
                    type="filepath",
                    label=UI["image"],
                    interactive=True,
                    visible=False,
                    buttons=[],
                    elem_classes=["camera-capture"],
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

            lat = gr.Number(visible=False)
            lon = gr.Number(visible=False)
            result_state = gr.State(value=None)
            dealer_page_state = gr.State(value=0)
            gr.HTML(f"<div class='disclaimer'>{UI['disclaimer']}</div>")

        demo.load(fn=None, inputs=None, outputs=[lat, lon], js=_GEO_JS)
        locate.click(fn=None, inputs=None, outputs=[lat, lon], js=_GEO_JS)
        theme.click(fn=None, outputs=theme, js=_THEME_JS, queue=False)
        photo_menu.click(
            lambda: gr.update(visible=True),
            outputs=photo_actions,
            show_progress="hidden",
            queue=False,
        )
        upload_image.upload(
            lambda path: (
                gr.update(value=path, visible=True),
                gr.update(visible=False),
            ),
            inputs=upload_image,
            outputs=[selected_image, photo_actions],
            show_progress="hidden",
        )
        camera_button.click(
            lambda: (
                gr.update(value=None, visible=True),
                gr.update(visible=False),
            ),
            outputs=[camera_capture, photo_actions],
            show_progress="hidden",
            queue=False,
        )
        camera_capture.input(
            _captured_image_state,
            inputs=camera_capture,
            outputs=[selected_image, camera_capture],
            show_progress="hidden",
        )
        text.change(
            _diagnose_button_state,
            inputs=text,
            outputs=submit,
            show_progress="hidden",
            queue=False,
        )
        submit.click(
            _show_analysis_loading,
            outputs=[response_card, response_text],
            show_progress="hidden",
        ).then(
            _on_submit,
            inputs=[language, audio, selected_image, text, lat, lon],
            outputs=[
                response_text,
                audio_out,
                user_text,
                user_image,
                text,
                audio,
                selected_image,
                result_state,
                dealer_page_state,
                dealer_pager,
                previous_dealers,
                next_dealers,
                dealer_page_label,
            ],
        ).then(
            lambda: (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            ),
            outputs=[user_card, response_card, photo_actions, camera_capture],
        )
        text.submit(
            _show_analysis_loading,
            outputs=[response_card, response_text],
            show_progress="hidden",
        ).then(
            _on_submit,
            inputs=[language, audio, selected_image, text, lat, lon],
            outputs=[
                response_text,
                audio_out,
                user_text,
                user_image,
                text,
                audio,
                selected_image,
                result_state,
                dealer_page_state,
                dealer_pager,
                previous_dealers,
                next_dealers,
                dealer_page_label,
            ],
        ).then(
            lambda: (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            ),
            outputs=[user_card, response_card, photo_actions, camera_capture],
        )
        previous_dealers.click(
            _previous_dealer_page,
            inputs=[result_state, dealer_page_state],
            outputs=[
                response_text,
                dealer_page_state,
                dealer_pager,
                previous_dealers,
                next_dealers,
                dealer_page_label,
            ],
            show_progress="hidden",
        )
        next_dealers.click(
            _next_dealer_page,
            inputs=[result_state, dealer_page_state],
            outputs=[
                response_text,
                dealer_page_state,
                dealer_pager,
                previous_dealers,
                next_dealers,
                dealer_page_label,
            ],
            show_progress="hidden",
        )

    return demo
