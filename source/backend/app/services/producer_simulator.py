"""
app/services/producer_simulator.py

Simule un flux d'avis clients arrivant en direct -- publie un avis
(pioche dans le VRAI dataset SemEval, Phase 9) sur Kafka a intervalle
regulier. Remplace un vrai site e-commerce, qu'on n'a pas dans ce
projet portfolio.

Demarre comme tache de fond au lancement du serveur (main.py),
exactement comme le consommateur -- producteur et consommateur
tournent tous les deux en continu, independamment.

Le pool d'avis (de vrais avis SemEval, plus credibles pour une demo
qu'un jeu de phrases inventees) est PRE-TELECHARGE AU BUILD de l'image
Docker (voir prefetch_review_pool.py) et lu ici depuis un JSON
statique -- ni `datasets` ni `scikit-learn` (necessaires a
load_semeval_absa()) ne sont installes au runtime (image finale
torch-free, meme raison que model_registry.py), et le runtime n'a plus
besoin d'acces reseau a huggingface.co pour ce pool."""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path

# Repli si le prefetch au build n'a pas eu lieu (ex. dev local sans
# avoir lance prefetch_review_pool.py) -- garantit que le simulateur
# fonctionne quand meme, avec un choix de phrases plus restreint.
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

# Chemin ABSOLU, resolu par rapport a ce fichier -- pas relatif au
# repertoire de travail du processus (meme raison que ONNX_MODELS_DIR
# dans model_registry.py : le cwd du conteneur ne correspond pas a
# source/backend/, --app-dir change seulement sys.path). Ce fichier
# vit dans app/services/, review_pool.json a la racine de
# source/backend/ -- deux niveaux plus haut.
REVIEW_POOL_PATH = Path(__file__).resolve().parents[2] / "review_pool.json"

_REVIEW_POOL_CACHE: list[str] | None = None


def load_review_pool() -> list[str]:
    """Charge (une seule fois, mis en cache) le pool d'avis SemEval
    pre-telecharge au build (voir prefetch_review_pool.py)."""
    global _REVIEW_POOL_CACHE
    if _REVIEW_POOL_CACHE is not None:
        return _REVIEW_POOL_CACHE

    try:
        with open(REVIEW_POOL_PATH, encoding="utf-8") as f:
            _REVIEW_POOL_CACHE = json.load(f)
        print(f"Pool d'avis SemEval charge : {len(_REVIEW_POOL_CACHE)} avis uniques")
    except (OSError, json.JSONDecodeError) as e:
        print(
            f"Echec du chargement de {REVIEW_POOL_PATH} ({e}), "
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
    pool_avis = await loop.run_in_executor(None, load_review_pool)

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
