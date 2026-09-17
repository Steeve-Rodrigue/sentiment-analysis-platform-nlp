"""
api/main.py

Point d'entree de l'API.

Le lifespan demarre TROIS choses au lancement :
1. Charge les modeles (registry.load_all())
2. Lance le PRODUCTEUR simule (avis fictifs publies en continu)
3. Lance le CONSOMMATEUR Kafka (analyse + diffusion, sans persistance)
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.model_registry import registry
from app.routers import analyze, live, sentiment
from app.services.kafka_service import run_kafka_consumer_loop
from app.services.local_stream_service import (
    run_local_consumer_loop,
    run_producer_simulator_loop_local,
)
from app.services.producer_simulator import run_producer_simulator_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_all()

    # settings.use_kafka picks which pipeline backs the live review
    # feed -- a real Kafka topic (local docker-compose, or a managed
    # Kafka in prod) when True, an in-process asyncio.Queue (e.g. on
    # Render, where no Kafka broker is available/managed) when False.
    # Same producer -> analyze -> broadcast pipeline either way, see
    # local_stream_service.py.
    if settings.use_kafka:
        producer_task = asyncio.create_task(
            run_producer_simulator_loop(
                settings.kafka_review_topic, settings.kafka_bootstrap_servers
            )
        )
        consumer_task = asyncio.create_task(
            run_kafka_consumer_loop(
                settings.kafka_review_topic,
                settings.kafka_bootstrap_servers,
                registry,
            )
        )
    else:
        review_queue: asyncio.Queue = asyncio.Queue()
        producer_task = asyncio.create_task(
            run_producer_simulator_loop_local(review_queue)
        )
        consumer_task = asyncio.create_task(
            run_local_consumer_loop(review_queue, registry)
        )

    yield

    producer_task.cancel()
    consumer_task.cancel()


app = FastAPI(title="GlobaTrend Insights API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sentiment.router)
app.include_router(analyze.router)
app.include_router(live.router)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "models_ready": registry.is_ready()}
