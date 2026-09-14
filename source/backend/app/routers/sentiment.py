"""
source/backend/app/routers/sentiment.py

POST /api/sentiment -- section "sentiment global" de la page
principale.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.model_registry import ModelRegistry
from app.dependencies import get_model_registry
from app.schemas.sentiment import SentimentRequest, SentimentResponse
from app.services.sentiment_service import analyze_sentiment

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.post("", response_model=SentimentResponse)
def sentiment(
    request: SentimentRequest,
    registry: ModelRegistry = Depends(get_model_registry),
) -> SentimentResponse:
    return analyze_sentiment(request.text, registry)
