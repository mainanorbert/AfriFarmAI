"""Pydantic data contracts shared across services, orchestration, and UI."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["sw", "luo", "en"]
"""Supported languages: Swahili (sw), Dholuo (luo), English (en)."""


class Severity(str, Enum):
    """Diagnosis severity used to drive UI emphasis and escalation copy."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class Subject(str, Enum):
    """Whether the case concerns a crop or an animal."""

    CROP = "crop"
    ANIMAL = "animal"
    UNKNOWN = "unknown"


class AnalyzeRequest(BaseModel):
    """A single farmer request: any of voice, image, or typed text."""

    language: Language = "sw"
    text: Optional[str] = None
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    county: Optional[str] = Field(
        default=None, description="Kenyan county used for dealer lookup."
    )


class Dealer(BaseModel):
    """An approved agro-dealer surfaced to the farmer."""

    name: str
    county: str
    town: str
    phone: str
    specialties: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_km: Optional[float] = None


class Diagnosis(BaseModel):
    """Structured diagnosis produced by the reasoning layer."""

    subject: Subject = Subject.UNKNOWN
    condition: str
    severity: Severity = Severity.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0)
    treatment: str
    prevention: str
    escalate: bool = Field(
        default=False, description="True when a professional should be consulted."
    )


class AnalyzeResult(BaseModel):
    """End-to-end result returned to the Gradio UI."""

    transcript: str
    language: Language
    diagnosis: Diagnosis
    localized_message: str
    audio_reply_path: Optional[str] = None
    dealers: list[Dealer] = Field(default_factory=list)
    low_confidence: bool = False
