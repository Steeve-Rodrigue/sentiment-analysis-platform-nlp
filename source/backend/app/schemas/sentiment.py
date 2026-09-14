"""
api/schemas/sentiment.py

Schemas pour POST /api/sentiment -- section "sentiment global" de la
page principale. Modele : DistilBERT fine-tune (Phase 6), binaire.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class SentimentResponse(BaseModel):
    text: str
    sentiment: Literal["positive", "negative"]
    confidence: float
    processing_time_ms: float
