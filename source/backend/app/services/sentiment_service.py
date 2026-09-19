"""
app/services/sentiment_service.py

Logique pour POST /api/sentiment -- utilise maintenant le modele ONNX
quantifie (ModelRegistry), avec des tenseurs NumPy plutot que
PyTorch. VERIFIE EMPIRIQUEMENT : return_tensors="np" fait revenir les
logits en numpy.ndarray, pas torch.Tensor -- torch n'est plus du tout
importe dans ce fichier, ni necessaire dans l'image finale au runtime.
"""

from __future__ import annotations

import time

import numpy as np

from app.core.model_registry import ModelRegistry
from app.schemas.sentiment import SentimentResponse


def _softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    return e / np.sum(e, axis=-1, keepdims=True)


def analyze_sentiment(text: str, registry: ModelRegistry) -> SentimentResponse:
    """Classifie le sentiment global d'un avis (positive/negative)."""
    start = time.perf_counter()

    inputs = registry.sentiment_tokenizer(
        text, return_tensors="np", truncation=True, max_length=512
    )
    onnx_inputs = {
        k: v for k, v in inputs.items() if k in registry.sentiment_input_names
    }
    (logits,) = registry.sentiment_session.run(None, onnx_inputs)
    probabilities = _softmax(logits)
    predicted_class = int(np.argmax(logits, axis=-1)[0])
    label = registry.sentiment_config.id2label[predicted_class]
    confidence = float(probabilities[0, predicted_class])

    elapsed_ms = (time.perf_counter() - start) * 1000
    return SentimentResponse(
        text=text,
        sentiment=label,
        confidence=confidence,
        processing_time_ms=elapsed_ms,
    )
