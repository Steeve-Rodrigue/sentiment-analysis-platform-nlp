"""
app/services/absa_service.py

Logique pour POST /api/aspects/analyze -- reutilise
extract_aspect_candidates() (Phase 9, inchange), mais la
classification passe maintenant par le modele ONNX quantifie, avec
des tenseurs NumPy plutot que PyTorch (meme raison que
sentiment_service.py -- reduire l'empreinte memoire sur Render).

predict_aspect_sentiment() ci-dessous est aussi reutilisee par le
pipeline live (kafka_service.py / local_stream_service.py), qui avait
avant besoin de la version PyTorch de src/aspect_sentiment/absa.py
(predict_aspect_sentiment_with_confidence, incompatible avec une
InferenceSession ONNX)."""

from __future__ import annotations

import time

import numpy as np

from app.core.model_registry import ModelRegistry
from app.schemas.analyze import AnalyzeResponse, AspectSentiment


def _softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    return e / np.sum(e, axis=-1, keepdims=True)


def predict_aspect_sentiment(
    text: str, aspect: str, registry: ModelRegistry
) -> tuple[str, float]:
    """Classifie le sentiment d'UN aspect via le modele ABSA ONNX
    quantifie -- renvoie (label, confidence)."""
    inputs = registry.absa_tokenizer(text, aspect, return_tensors="np", truncation=True)
    onnx_inputs = {k: v for k, v in inputs.items() if k in registry.absa_input_names}
    (logits,) = registry.absa_session.run(None, onnx_inputs)
    probabilities = _softmax(logits)
    predicted_class = int(np.argmax(logits, axis=-1)[0])
    label = registry.absa_config.id2label[predicted_class]
    confidence = float(probabilities[0, predicted_class])
    return label, confidence


def predict_aspects_with_confidence(
    text: str, aspects: list[str], registry: ModelRegistry
) -> dict[str, tuple[str, float]]:
    """Comme predict_aspect_sentiment(), mais pour plusieurs aspects
    d'un coup -- {aspect: (sentiment, confidence)}. Utilisee par le
    pipeline live (kafka_service.py / local_stream_service.py), qui
    avait besoin avant de l'equivalent PyTorch de
    src/aspect_sentiment/absa.py (predict_aspect_sentiment_with_confidence,
    incompatible avec une InferenceSession ONNX)."""
    return {
        aspect: predict_aspect_sentiment(text, aspect, registry) for aspect in aspects
    }


def analyze_aspects(
    text: str,
    registry: ModelRegistry,
    aspects: list[str] | None = None,
) -> AnalyzeResponse:
    """Extrait les aspects (si non fournis) et predit le sentiment de
    chacun, via le modele ONNX quantifie."""
    from aspect_sentiment.absa import extract_aspect_candidates

    start = time.perf_counter()
    aspects_to_use = aspects or extract_aspect_candidates(text)

    if not aspects_to_use:
        return AnalyzeResponse(
            text=text,
            aspects=[],
            confidence=0.0,
            processing_time_ms=(time.perf_counter() - start) * 1000,
        )

    aspect_sentiments = []
    confidences = []
    for aspect in aspects_to_use:
        label, confidence = predict_aspect_sentiment(text, aspect, registry)
        aspect_sentiments.append(AspectSentiment(aspect=aspect, sentiment=label))
        confidences.append(confidence)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return AnalyzeResponse(
        text=text,
        aspects=aspect_sentiments,
        confidence=sum(confidences) / len(confidences),
        processing_time_ms=elapsed_ms,
    )
