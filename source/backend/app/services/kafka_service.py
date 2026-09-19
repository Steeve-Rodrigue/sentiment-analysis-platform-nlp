"""
source/backend/app/services/kafka_service.py

Tache de fond qui consomme Kafka en continu, des le demarrage du
serveur -- simule un flux d'avis clients arrivant en direct. Analyse
chaque avis (Phase 9) puis le DIFFUSE aux clients connectes sur
/api/live (broadcast.py). AUCUNE PERSISTANCE -- rien n'est enregistre
nulle part, le message existe seulement le temps de sa diffusion.

kafka-python est SYNCHRONE (bloquant) -- execute dans un thread
separe (run_in_executor) pour ne pas geler la boucle asyncio de
FastAPI.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.model_registry import ModelRegistry
from app.schemas.analyze import AspectSentiment
from app.schemas.live import LiveReviewMessage
from app.services.absa_service import predict_aspects_with_confidence
from app.services.broadcast import broadcaster

_SENTIMENT_SIGN = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}


def compute_overall_score(
    sentiments: dict[str, tuple[str, float]],
) -> float:
    """Moyenne, sur tous les aspects, de la confiance du modele
    signee par le sens du sentiment (+confidence si positive,
    -confidence si negative, 0 si neutral) -- c'est CE nombre qui est
    trace point par point sur le graphe en temps reel du frontend, a
    mesure que les avis arrivent. Un avis sans aspect detecte (dict
    vide) obtient un score neutre (0.0) plutot qu'une division par
    zero."""
    if not sentiments:
        return 0.0
    scores = [
        _SENTIMENT_SIGN[label] * confidence for label, confidence in sentiments.values()
    ]
    return sum(scores) / len(scores)


async def run_kafka_consumer_loop(
    topic: str,
    bootstrap_servers: str,
    registry: ModelRegistry,
) -> None:
    """Boucle infinie : consomme Kafka, analyse, diffuse. Demarree
    une seule fois au lancement du serveur (lifespan de main.py)."""
    from aspect_sentiment.absa import extract_aspect_candidates
    from realtime.streaming import create_consumer

    loop = asyncio.get_event_loop()
    consumer = await loop.run_in_executor(
        None, create_consumer, topic, bootstrap_servers
    )

    try:
        while True:
            message = await loop.run_in_executor(None, lambda: next(iter(consumer)))
            review = message.value

            aspects = await loop.run_in_executor(
                None, extract_aspect_candidates, review["text"]
            )
            sentiments = await loop.run_in_executor(
                None,
                predict_aspects_with_confidence,
                review["text"],
                aspects,
                registry,
            )
            aspect_sentiments = [
                AspectSentiment(aspect=a, sentiment=label)
                for a, (label, _confidence) in sentiments.items()
            ]

            # DIFFUSION uniquement -- pas d'ecriture en base
            await broadcaster.publish(
                LiveReviewMessage(
                    review_id=review["review_id"],
                    text=review["text"],
                    aspect_sentiments=aspect_sentiments,
                    overall_score=compute_overall_score(sentiments),
                    received_at=datetime.now(timezone.utc).isoformat(),
                )
            )
    finally:
        consumer.close()
