"""Provider error types used to surface honest failures to the farmer."""

from __future__ import annotations


class ProviderError(Exception):
    """A real provider call failed (missing key, network, or bad response).

    ``stage`` names the pipeline step ("transcription", "diagnosis", …) so the
    orchestration layer can show a clear, localized message instead of fake data.
    """

    def __init__(self, stage: str, detail: str = ""):
        self.stage = stage
        self.detail = detail
        super().__init__(f"{stage} failed" + (f": {detail}" if detail else ""))
