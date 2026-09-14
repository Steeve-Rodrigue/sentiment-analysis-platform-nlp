"""
api/schemas/live.py

Schema pour le WebSocket /api/live -- flux Kafka SIMULE, analyse et
diffuse en direct, SANS AUCUNE PERSISTANCE.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.analyze import AspectSentiment


class LiveReviewMessage(BaseModel):
    review_id: int
    text: str
    aspect_sentiments: list[AspectSentiment]
    overall_score: float = Field(
        ge=-1,
        le=1,
        description=(
            "Moyenne, sur tous les aspects, de la confiance du "
            "modele signee par le sens du sentiment (+confidence si "
            "positive, -confidence si negative, 0 si neutral) -- LE "
            "point trace sur le graphe en temps reel du frontend, "
            "calcule ici pour que le frontend n'ait qu'a afficher, "
            "pas a recalculer."
        ),
    )
    received_at: str
