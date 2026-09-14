"""
api/dependencies.py

Dependance FastAPI partagee -- injecte le registre de modeles. Plus
de connexion DB : aucune persistance dans ce projet.
"""

from __future__ import annotations

from app.core.model_registry import ModelRegistry, registry


def get_model_registry() -> ModelRegistry:
    return registry
