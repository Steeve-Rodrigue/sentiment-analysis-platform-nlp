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
from app.services.producer_simulator import run_producer_simulator_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_all()

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
