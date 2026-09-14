"""
source/backend/app/schemas/analyze.py

Schemas pour POST /api/aspects/analyze -- section "aspects" de la
page principale. Modele : ABSA (Phase 9), classification jointe
(texte, aspect) -> sentiment.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    aspects: list[str] | None = Field(
        default=None,
        description=(
            "Aspects a evaluer explicitement. Si omis, extraits "
            "automatiquement via extract_aspect_candidates (Phase 9)."
        ),
    )


class AspectSentiment(BaseModel):
    aspect: str
    sentiment: Literal["positive", "negative", "neutral"]


class AnalyzeResponse(BaseModel):
    text: str
    aspects: list[AspectSentiment]
    confidence: float
    processing_time_ms: float
