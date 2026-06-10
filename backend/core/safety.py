"""Post-processing safety rules applied to every diagnosis.

Enforces cautious behaviour: gate low-confidence results, escalate severe
or animal cases to professionals, and never let an empty treatment reach the
farmer.
"""

from __future__ import annotations

from backend.core.config import settings
from backend.core.models import Diagnosis, Severity, Subject

_SAFE_FALLBACK = (
    "We could not confirm the problem from what was shared. Please send a "
    "clearer photo and describe what you see, or contact your nearest "
    "agro-dealer or extension officer for help."
)


def apply_safety(diagnosis: Diagnosis) -> tuple[Diagnosis, bool]:
    """Return a safety-adjusted diagnosis and a low-confidence flag.

    A diagnosis below the configured confidence threshold is replaced with a
    cautious fallback. Severe cases — and any animal case, which can escalate
    quickly — are marked for professional escalation.
    """

    low_confidence = diagnosis.confidence < settings.min_confidence

    if low_confidence:
        diagnosis = diagnosis.model_copy(
            update={
                "condition": "Needs review",
                "severity": Severity.UNKNOWN,
                "treatment": _SAFE_FALLBACK,
                "prevention": "",
                "escalate": True,
            }
        )
        return diagnosis, True

    escalate = diagnosis.severity == Severity.SEVERE or diagnosis.subject == Subject.ANIMAL
    if escalate and not diagnosis.escalate:
        diagnosis = diagnosis.model_copy(update={"escalate": True})

    return diagnosis, False
