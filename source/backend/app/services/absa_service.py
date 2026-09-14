"""
source/backend/app/services/absa_service.py

Logique pour POST /api/aspects/analyze -- reutilise DIRECTEMENT les
fonctions de la Phase 9 (aspect_sentiment.absa). Section separee du
sentiment global (sentiment_service.py) -- deux champs distincts sur
la page principale, deux modeles distincts.
"""

from __future__ import annotations

import time

from app.core.model_registry import ModelRegistry
from app.schemas.analyze import AnalyzeResponse, AspectSentiment


def analyze_aspects(
    text: str,
    registry: ModelRegistry,
    aspects: list[str] | None = None,
) -> AnalyzeResponse:
    """Extrait les aspects (si non fournis) et predit le sentiment de
    chacun. Reutilise extract_aspect_candidates() et
    predict_aspect_sentiment_with_confidence() de la Phase 9 telles
    quelles."""
    from aspect_sentiment.absa import (
        extract_aspect_candidates,
        predict_aspect_sentiment_with_confidence,
    )

    start = time.perf_counter()
    aspects_to_use = aspects or extract_aspect_candidates(text)

    if not aspects_to_use:
        return AnalyzeResponse(
            text=text,
            aspects=[],
            confidence=0.0,
            processing_time_ms=(time.perf_counter() - start) * 1000,
        )

    raw_results = predict_aspect_sentiment_with_confidence(
        text, aspects_to_use, registry.absa_model, registry.absa_tokenizer
    )
    aspect_sentiments = [
        AspectSentiment(aspect=a, sentiment=label)
        for a, (label, _confidence) in raw_results.items()
    ]
    confidence = sum(c for _, c in raw_results.values()) / len(raw_results)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return AnalyzeResponse(
        text=text,
        aspects=aspect_sentiments,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
    )
