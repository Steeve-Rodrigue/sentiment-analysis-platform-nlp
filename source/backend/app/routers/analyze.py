"""
source/backend/app/routers/analyze.py

POST /api/aspects/analyze -- section "aspects" de la page principale.
Sans etat, comme /api/sentiment -- deux champs independants.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.model_registry import ModelRegistry
from app.dependencies import get_model_registry
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.absa_service import analyze_aspects

router = APIRouter(prefix="/api/aspects", tags=["aspects"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    registry: ModelRegistry = Depends(get_model_registry),
) -> AnalyzeResponse:
    return analyze_aspects(request.text, registry, aspects=request.aspects)
