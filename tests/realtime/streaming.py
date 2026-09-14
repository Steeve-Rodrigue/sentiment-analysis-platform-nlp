"""
tests/realtime/test_streaming.py

Tests unitaires pour src/realtime/streaming.py.

Necessitent un broker Kafka reellement en cours d'execution (voir
docker/docker-compose.yml) -- marques @pytest.mark.kafka, distinct de
@pytest.mark.network (ici il ne s'agit pas d'un simple acces internet,
mais d'un SERVICE qui doit tourner). Lancer explicitement avec :
    uv run pytest tests/ -v -m kafka
apres avoir demarre le broker :
    docker compose -f docker/docker-compose.yml up -d
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest


@pytest.mark.kafka
def test_producer_can_connect_and_publish():
    from realtime.streaming import create_producer, publish_review

    producer = create_producer()
    publish_review(producer, "test-topic", "Great delivery!", review_id=1)
    producer.close()


@pytest.mark.kafka
def test_consumer_receives_published_message():
    from realtime.streaming import (
        create_consumer,
        create_producer,
        publish_review,
    )

    producer = create_producer()
    publish_review(
        producer,
        "test-topic-2",
        "The product quality is excellent",
        review_id=42,
    )
    producer.close()

    consumer = create_consumer("test-topic-2")
    message = next(iter(consumer))
    assert message.value["review_id"] == 42
    assert "quality" in message.value["text"]
    consumer.close()


@pytest.mark.kafka
def test_consume_and_analyze_produces_aspect_sentiments():
    from aspect_sentiment.absa import load_absa_classifier
    from realtime.streaming import (
        consume_and_analyze,
        create_consumer,
        create_producer,
        publish_review,
    )

    producer = create_producer()
    publish_review(
        producer,
        "test-topic-3",
        "The delivery was fast but the price is too high",
        review_id=7,
    )
    producer.close()

    model, tokenizer = load_absa_classifier()
    consumer = create_consumer("test-topic-3")

    results = consume_and_analyze(consumer, model, tokenizer, max_messages=1)
    consumer.close()

    assert len(results) == 1
    assert results[0]["review_id"] == 7
    assert len(results[0]["aspect_sentiments"]) > 0
