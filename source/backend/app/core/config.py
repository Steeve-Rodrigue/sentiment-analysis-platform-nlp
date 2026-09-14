"""
api/core/config.py

Parametres centralises de l'API -- chemins de modeles, hote Kafka,
etc. Un seul endroit a modifier pour passer de dev a prod.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Classe de configuration pour l'application FastAPI.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Nom de l'application
    app_name: str = "Sentiment Analysis Platform"
    # Version de l'application
    app_version: str = "1.0.0"

    absa_model_name: str = "distilbert-base-uncased"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_review_topic: str = "customer-reviews"
    cors_allowed_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
