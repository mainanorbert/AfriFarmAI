import gradio as gr

from backend.core.config import get_settings
from backend.services.nvidia_chat_client import NvidiaChatClient, NvidiaChatError


def respond(
    prompt: str,
    history: list[dict[str, str]] | None,
) -> tuple[str, list[dict[str, str]]]:
    """Send one prompt to NVIDIA and append its answer to UI-only history."""
    history = history or []
    prompt = prompt.strip()
    if not prompt:
        return "", history

    try:
        answer = NvidiaChatClient(get_settings()).chat(prompt)
    except (NvidiaChatError, RuntimeError):
        answer = "The model is unavailable. Check the NVIDIA settings and try again."

    return "", history + [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": answer},
    ]


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="AfriFarmAI Chat") as demo:
        gr.Markdown("# AfriFarmAI Chat")
        chatbot = gr.Chatbot(type="messages", label="Conversation")
        prompt = gr.Textbox(
            label="Prompt",
            placeholder="Ask the model something...",
        )
        send = gr.Button("Send", variant="primary")

        send.click(respond, [prompt, chatbot], [prompt, chatbot])
        prompt.submit(respond, [prompt, chatbot], [prompt, chatbot])
    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="0.0.0.0", server_port=7860, share=True)
