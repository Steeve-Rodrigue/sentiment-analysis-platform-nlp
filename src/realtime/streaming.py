"""
src/realtime/streaming.py

Phase 10 -- Temps reel -- producteur/consommateur Kafka.

Theorie resumee (voir la conversation associee pour le detail) :

Tout ce qui a ete construit jusqu'ici traite des avis PAR LOTS (un
dataset entier charge d'un coup). En production reelle, les avis
arrivent EN CONTINU. Kafka decouple deux roles via une file nommee
(un "topic") :

    [Producteur] --publie--> [Topic Kafka] --lit--> [Consommateur]

Le producteur ne sait pas qui consomme, le consommateur ne sait pas
qui produit -- ils communiquent uniquement via le topic. Ca permet au
consommateur de traiter les messages A SON RYTHME, meme si le
producteur en envoie plus vite qu'on ne peut les analyser.

NECESSITE un broker Kafka reellement en cours d'execution -- pas
seulement un acces reseau comme pour Hugging Face, un vrai SERVICE qui
tourne en continu. Voir docker/docker-compose.yml (fourni a part) pour
lancer un broker local via Docker. Aucun broker n'est disponible dans
le sandbox utilise pour ecrire ce code -- a verifier chez vous apres
avoir lance `docker compose -f docker/docker-compose.yml up -d`.
"""

from __future__ import annotations

import json


def create_producer(bootstrap_servers: str = "localhost:9092"):
    """Cree un producteur Kafka, pret a publier des messages JSON.
    value_serializer convertit automatiquement un dict Python en JSON
    encode -- chaque message publie sera un avis client serialise."""
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def publish_review(producer, topic: str, review_text: str, review_id: int):
    """Publie UN avis client sur le topic Kafka -- simule un avis qui
    vient d'arriver en direct, plutot qu'un dataset deja complet."""
    message = {"review_id": review_id, "text": review_text}
    producer.send(topic, value=message)
    producer.flush()


def create_consumer(topic: str, bootstrap_servers: str = "localhost:9092"):
    """Cree un consommateur Kafka, abonne au topic. auto_offset_reset
    ="earliest" : si le consommateur demarre APRES que des messages
    aient deja ete publies, il les lit depuis le debut plutot que de
    les ignorer -- important pour ne rater aucun avis."""
    from kafka import KafkaConsumer

    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
    )


def consume_and_analyze(consumer, absa_model, absa_tokenizer, max_messages=None):
    """Boucle de consommation : lit chaque avis publie sur le topic,
    extrait ses aspects candidats, predit le sentiment de chacun --
    reutilise directement extract_aspect_candidates() et
    predict_aspect_sentiment() de la Phase 9 (aspect_sentiment/absa.py),
    aucune nouvelle logique de classification a ecrire ici.

    max_messages limite le nombre de messages traites avant de
    s'arreter -- utile pour un test/une demo, sinon la boucle tourne
    indefiniment (comportement normal d'un vrai consommateur en
    production, qui reste actif en permanence)."""
    from aspect_sentiment.absa import (
        extract_aspect_candidates,
        predict_aspect_sentiment,
    )

    results = []
    for count, message in enumerate(consumer):
        review = message.value
        aspects = extract_aspect_candidates(review["text"])
        sentiments = predict_aspect_sentiment(
            review["text"], aspects, absa_model, absa_tokenizer
        )
        results.append(
            {
                "review_id": review["review_id"],
                "text": review["text"],
                "aspect_sentiments": sentiments,
            }
        )

        if max_messages is not None and count + 1 >= max_messages:
            break

    return results
