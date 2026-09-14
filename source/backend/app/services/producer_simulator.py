"""
app/services/producer_simulator.py

Simule un flux d'avis clients arrivant en direct -- publie un avis
(pioche dans le VRAI dataset SemEval, Phase 9) sur Kafka a intervalle
regulier. Remplace un vrai site e-commerce, qu'on n'a pas dans ce
projet portfolio.

Demarre comme tache de fond au lancement du serveur (main.py),
exactement comme le consommateur -- producteur et consommateur
tournent tous les deux en continu, independamment.

Reutilise load_semeval_absa() (Phase 9) plutot que des phrases
inventees a la main -- de vrais avis annotes par des humains, plus
credibles pour une demo. Necessite un acces reseau pour telecharger le
dataset au premier appel (mis en cache ensuite, voir _load_review_pool).
"""

from __future__ import annotations

import asyncio
import random

# Repli en cas d'echec du chargement du dataset (ex. pas de reseau au
# demarrage du serveur) -- garantit que le simulateur fonctionne quand
# meme, avec un choix de phrases plus restreint.
FALLBACK_REVIEWS = [
    "The delivery was super fast, arrived the next day",
    "Product quality is outstanding, highly recommend it",
    "Customer service took forever to respond to my email",
    "Packaging was damaged but the product inside was fine",
    "Refund process was quick and completely painless",
    "The website checkout process was confusing and slow",
    "Great product overall but the price feels a bit high",
    "Warranty claim was handled professionally and quickly",
    "Shipping took much longer than expected this time",
    "Absolutely love this purchase, exceeded my expectations",
]

_REVIEW_POOL_CACHE: list[str] | None = None


def _load_review_pool() -> list[str]:
    """Charge (une seule fois, mis en cache) l'ensemble des phrases
    reelles du dataset SemEval ABSA -- train + eval reunis. Un meme
    avis peut apparaitre plusieurs fois dans le dataset brut (une
    ligne par aspect detecte dans cet avis) -- dict.fromkeys()
    deduplique tout en preservant l'ordre d'apparition."""
    global _REVIEW_POOL_CACHE
    if _REVIEW_POOL_CACHE is not None:
        return _REVIEW_POOL_CACHE

    try:
        from aspect_sentiment.absa import load_semeval_absa

        (train_texts, _, _, eval_texts, _, _) = load_semeval_absa()
        tous_les_textes = train_texts + eval_texts
        _REVIEW_POOL_CACHE = list(dict.fromkeys(tous_les_textes))
        print(
            f"Pool d'avis SemEval charge : " f"{len(_REVIEW_POOL_CACHE)} avis uniques"
        )
    except Exception as e:
        print(
            f"Echec du chargement de SemEval ({e}), "
            f"repli sur {len(FALLBACK_REVIEWS)} avis fixes"
        )
        _REVIEW_POOL_CACHE = FALLBACK_REVIEWS

    return _REVIEW_POOL_CACHE


async def run_producer_simulator_loop(
    topic: str,
    bootstrap_servers: str,
    interval_seconds: float = 5.0,
) -> None:
    """Publie un avis aleatoire (pioche dans le vrai dataset SemEval)
    toutes les interval_seconds secondes, en continu -- simule des
    avis clients arrivant naturellement."""
    from realtime.streaming import create_producer, publish_review

    loop = asyncio.get_event_loop()
    producer = await loop.run_in_executor(None, create_producer, bootstrap_servers)

    # charge le pool AVANT la boucle (telechargement potentiel du
    # dataset ne doit se faire qu'une fois, pas a chaque iteration)
    pool_avis = await loop.run_in_executor(None, _load_review_pool)

    review_id = 0
    try:
        while True:
            review_id += 1
            text = random.choice(pool_avis)
            await loop.run_in_executor(
                None, publish_review, producer, topic, text, review_id
            )
            await asyncio.sleep(interval_seconds)
    finally:
        producer.close()
