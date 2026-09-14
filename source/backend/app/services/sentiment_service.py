"""
source/backend/app/services/sentiment_service.py

Logique pour POST /api/sentiment -- sentiment GLOBAL (pas par
aspect), reutilise DIRECTEMENT le modele DistilBERT fine-tune en
Phase 6. Aucune nouvelle logique de classification.
"""

from __future__ import annotations

import time

import torch

from app.core.model_registry import ModelRegistry
from app.schemas.sentiment import SentimentResponse


def analyze_sentiment(text: str, registry: ModelRegistry) -> SentimentResponse:
    """Classifie le sentiment global d'un avis (positive/negative),
    exactement le modele et la logique construits/verifies en
    Phase 6."""
    start = time.perf_counter()

    inputs = registry.sentiment_tokenizer(
        text, return_tensors="pt", truncation=True, max_length=512
    )
    with torch.no_grad():
        logits = registry.sentiment_model(**inputs).logits
    probabilities = torch.softmax(logits, dim=-1)
    predicted_class = torch.argmax(logits, dim=-1).item()
    label = registry.sentiment_model.config.id2label[predicted_class]
    confidence = probabilities[0, predicted_class].item()

    elapsed_ms = (time.perf_counter() - start) * 1000
    return SentimentResponse(
        text=text,
        sentiment=label,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
    )
