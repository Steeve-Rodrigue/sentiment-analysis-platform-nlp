"""
source/backend/app/services/local_stream_service.py

Version SANS Kafka du pipeline producteur/consommateur -- pour la
production (ex. Render) ou aucun broker Kafka n'est disponible/gere.

Le producteur simule (producer_simulator.py) et le consommateur
(kafka_service.py) tournent tous les deux DANS CE MEME processus
FastAPI (voir main.py::lifespan) -- Kafka ne decouple donc pas deux
services distincts ici, juste deux taches du meme processus qui se
parlent via un topic. Remplace ce hop par une asyncio.Queue en
memoire : meme pipeline (producteur -> analyse -> diffusion), un
service externe de moins a deployer/payer/faire tomber en panne.

Reutilise directement load_review_pool() (producer_simulator.py) et
compute_overall_score() (kafka_service.py) -- seule la maniere de faire
transiter un avis du producteur au consommateur change, pas le reste
du pipeline.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from app.core.model_registry import ModelRegistry
from app.schemas.analyze import AspectSentiment
from app.schemas.live import LiveReviewMessage
from app.services.absa_service import predict_aspects_with_confidence
from app.services.broadcast import broadcaster
from app.services.kafka_service import compute_overall_score
from app.services.producer_simulator import load_review_pool


async def run_producer_simulator_loop_local(
    queue: asyncio.Queue,
    interval_seconds: float = 5.0,
) -> None:
    """Equivalent sans Kafka de run_producer_simulator_loop() -- pousse
    un avis aleatoire sur la queue en memoire au lieu de le publier sur
    un topic Kafka."""
    loop = asyncio.get_event_loop()
    # charge le pool AVANT la boucle (telechargement potentiel du
    # dataset ne doit se faire qu'une fois, pas a chaque iteration)
    pool_avis = await loop.run_in_executor(None, load_review_pool)

    review_id = 0
    while True:
        review_id += 1
        text = random.choice(pool_avis)
        await queue.put({"review_id": review_id, "text": text})
        await asyncio.sleep(interval_seconds)


async def run_local_consumer_loop(
    queue: asyncio.Queue,
    registry: ModelRegistry,
) -> None:
    """Equivalent sans Kafka de run_kafka_consumer_loop() -- lit les
    avis depuis la queue en memoire au lieu d'un topic Kafka, exactement
    la meme logique d'analyse et de diffusion ensuite."""
    from aspect_sentiment.absa import extract_aspect_candidates

    loop = asyncio.get_event_loop()
    while True:
        review = await queue.get()

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
