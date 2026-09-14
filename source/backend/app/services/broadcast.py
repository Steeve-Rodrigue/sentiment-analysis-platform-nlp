"""
source/backend/app/services/broadcast.py

Diffuseur en memoire : permet a PLUSIEURS clients WebSocket (/live)
d'observer le MEME flux d'avis analyses, sans que chacun ne consomme
Kafka independamment (ce qui dupliquerait le travail et compliquerait
la coordination avec la persistance).

Le consommateur Kafka (kafka_service.py) publie ICI apres avoir
persiste chaque avis -- /live ne fait qu'ecouter ce diffuseur, jamais
Kafka directement.
"""

from __future__ import annotations

import asyncio

from app.schemas.live import LiveReviewMessage


class LiveBroadcaster:
    """Registre des clients WebSocket actuellement connectes a /live.
    publish() envoie un message a TOUS les clients connectes au moment
    de l'appel -- les clients qui se connectent APRES ne recoivent que
    les messages futurs (comportement normal d'un flux live, pas d'un
    historique)."""

    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def publish(self, message: LiveReviewMessage) -> None:
        for queue in list(self._subscribers):
            await queue.put(message)


# Instance unique, partagee entre la tache de fond Kafka et les
# connexions WebSocket
broadcaster = LiveBroadcaster()
