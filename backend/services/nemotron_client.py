"""Diagnosis reasoning + image understanding via Nemotron 3 Nano Omni.

In Path A this single 30B-A3B omni model handles the crop/animal image *and*
the symptom reasoning, so no separate vision model is required. The stub maps
common symptom keywords to representative diagnoses so the demo is responsive.
"""

from __future__ import annotations

from typing import Optional

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis, Severity, Subject

log = get_logger("services.nemotron")

# Minimal keyword → diagnosis map for the stub path (English/Swahili cues).
_RULES: list[tuple[tuple[str, ...], Diagnosis]] = [
    (
        ("mahindi", "maize", "bel", "madoa", "spot", "manjano", "yellow"),
        Diagnosis(
            subject=Subject.CROP,
            condition="Maize Lethal Necrosis (MLN)",
            severity=Severity.MODERATE,
            confidence=0.72,
            treatment=(
                "Remove and destroy badly affected plants. Control insect "
                "vectors (thrips, aphids) with an approved insecticide and "
                "avoid moving infected material between fields."
            ),
            prevention=(
                "Plant certified disease-free seed, rotate with non-cereal "
                "crops, and keep fields weed-free to reduce vectors."
            ),
        ),
    ),
    (
        ("worm", "funza", "kiwavi", "holes", "mashimo"),
        Diagnosis(
            subject=Subject.CROP,
            condition="Fall Armyworm",
            severity=Severity.MODERATE,
            confidence=0.69,
            treatment=(
                "Scout early; apply an approved biopesticide or insecticide "
                "into the leaf whorl in the evening. Handpick egg masses where "
                "feasible."
            ),
            prevention=(
                "Plant early and uniformly, intercrop with legumes, and "
                "encourage natural predators."
            ),
        ),
    ),
    (
        ("ng'ombe", "cow", "cattle", "diho", "homa", "fever", "animal"),
        Diagnosis(
            subject=Subject.ANIMAL,
            condition="Suspected East Coast Fever",
            severity=Severity.SEVERE,
            confidence=0.66,
            treatment=(
                "This can be fatal quickly. Contact a veterinarian urgently. "
                "Keep the animal shaded and hydrated while you arrange care."
            ),
            prevention=(
                "Control ticks with regular dipping/spraying and consider "
                "vaccination where available."
            ),
            escalate=True,
        ),
    ),
]

_DEFAULT = Diagnosis(
    subject=Subject.UNKNOWN,
    condition="Unclear",
    severity=Severity.UNKNOWN,
    confidence=0.30,
    treatment="",
    prevention="",
)


def diagnose(symptom_text: str, image_path: Optional[str] = None) -> Diagnosis:
    """Produce a structured diagnosis from symptom text and optional image.

    The omni model is multimodal; on the stub path the image is acknowledged
    but the match is driven by symptom keywords for determinism.
    """

    if not settings.use_real_models:
        has_image = bool(image_path)
        haystack = symptom_text.lower()
        for keywords, diagnosis in _RULES:
            if any(k in haystack for k in keywords):
                log.info(
                    "diagnose stub op=reason matched=1 image=%s", has_image
                )
                # An accompanying image nudges confidence up slightly.
                if has_image:
                    return diagnosis.model_copy(
                        update={"confidence": min(diagnosis.confidence + 0.08, 0.95)}
                    )
                return diagnosis
        log.info("diagnose stub op=reason matched=0 image=%s", has_image)
        return _DEFAULT

    # TODO(real): call Nemotron Omni (NVIDIA build.nvidia.com) with image+text
    #   and a JSON-only prompt; parse into Diagnosis. Enforce schema strictly.
    raise NotImplementedError("Real Nemotron not wired yet; set USE_REAL_MODELS=false.")
