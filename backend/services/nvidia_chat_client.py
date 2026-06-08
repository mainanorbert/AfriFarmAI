from openai import OpenAI, OpenAIError

from backend.core.config import Settings


class NvidiaChatError(RuntimeError):
    """Raised when NVIDIA cannot return a usable chat response."""


class NvidiaChatClient:
    """Thin client for NVIDIA's OpenAI-compatible chat API."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.nvidia_model_name
        self._client = OpenAI(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key,
        )

    def chat(self, prompt: str) -> str:
        try:
            completion = self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                top_p=0.95,
                max_tokens=4096,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": True},
                    "reasoning_budget": 2048,
                },
                stream=False,
            )
            answer = completion.choices[0].message.content
        except (OpenAIError, IndexError, TypeError) as exc:
            raise NvidiaChatError("NVIDIA chat request failed") from exc

        if not answer or not answer.strip():
            raise NvidiaChatError("NVIDIA returned an empty answer")
        return answer.strip()
