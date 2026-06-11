"""Pydantic data contracts shared across services, orchestration, and UI."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["sw", "en"]
"""Supported languages: Swahili (sw) and English (en)."""


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
    lat: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Farmer GPS latitude for nearest-dealer ranking.",
    )
    lon: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Farmer GPS longitude for nearest-dealer ranking.",
    )


class Dealer(BaseModel):
    """A nearby agrovet or agricultural supplier returned by Google Places."""

    name: str
    address: str
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    phone: Optional[str] = None
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    distance_km: float = Field(ge=0)
    maps_link: str


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
    dealer_search_status: Literal[
        "not_requested", "location_required", "success", "no_results", "error"
    ] = "not_requested"
    dealer_search_radius_km: Optional[int] = None
    low_confidence: bool = False
