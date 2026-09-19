# source/backend/Dockerfile
#
# Build MULTI-ETAPES, avec un changement important par rapport a la
# version precedente : l'etape FINALE n'installe PLUS torch du tout.
#
# POURQUOI : sur Render (tier gratuit, 512 Mo de RAM), PyTorch +
# Transformers + 2 modeles DistilBERT fp32 depassaient le quota.
# Solution : exporter les modeles en ONNX + les quantifier en int8 au
# BUILD (ou torch est encore necessaire, pour la conversion), puis ne
# garder qu'onnxruntime (beaucoup plus leger) au RUNTIME -- verifie
# empiriquement : reduction de taille des modeles de 75%, et
# l'inference fonctionne sans importer torch (return_tensors="np").

# ---------- ETAPE 1 : builder (a besoin de torch pour l'export) ----------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

COPY src/ /app/src/
COPY source/backend/app/ /app/backend/app/
COPY source/backend/export_and_quantize_models.py /app/backend/export_and_quantize_models.py
COPY source/backend/prefetch_review_pool.py /app/backend/prefetch_review_pool.py

ENV PYTHONPATH=/app/src
WORKDIR /app/backend
RUN uv run python export_and_quantize_models.py
# Pre-telecharge le pool d'avis SemEval (voir prefetch_review_pool.py)
# -- comme les modeles ONNX, calcule UNE FOIS au build (torch/datasets/
# sklearn/reseau disponibles ici), lu comme un simple JSON statique au
# runtime (app/services/producer_simulator.py).
RUN uv run python prefetch_review_pool.py

# ---------- ETAPE 2 : image finale, SANS torch ----------
FROM python:3.11-slim AS final

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# IMPORTANT : ce pyproject.toml est celui de source/backend/ (un
# fichier DIFFERENT du pyproject.toml a la racine du projet, qui lui
# garde torch/transformers[torch] pour l'entrainement) -- ne liste
# QUE ce qui est necessaire au runtime (fastapi, onnxruntime,
# transformers SANS torch). Les deux fichiers portent le meme nom mais
# vivent dans des dossiers differents, sans conflit. Pas de `optimum`
# ici non plus -- verifie empiriquement que ce paquet declare `torch`
# comme dependance INCONDITIONNELLE (meme sans extra), ce qui aurait
# reintroduit torch + un stack CUDA complet dans cette image "sans
# torch". Les modeles ONNX sont charges via onnxruntime.InferenceSession
# directement (app/core/model_registry.py).
COPY source/backend/pyproject.toml /app/pyproject.toml
COPY source/backend/uv.lock /app/uv.lock
RUN uv sync --frozen --no-dev

# NLTK : uniquement les 2 paquets dont extract_aspect_candidates() a
# reellement besoin (word_tokenize + pos_tag) -- pas
# scripts/setup_nltk.py (qui telecharge aussi spaCy + plusieurs Go de
# donnees NLTK non utilisees au runtime de l'API).
ENV NLTK_DATA=/app/nltk_data
RUN uv run python -m nltk.downloader -d "$NLTK_DATA" punkt_tab averaged_perceptron_tagger_eng

COPY --from=builder /app/backend/onnx_models /app/backend/onnx_models
COPY --from=builder /app/backend/review_pool.json /app/backend/review_pool.json
COPY --from=builder /app/backend/app /app/backend/app
# Seul src/aspect_sentiment/ (extract_aspect_candidates) est necessaire
# au runtime -- le reste de src/ (deep_learning, llms, multilingual,
# classical_ml, embeddings, transformers_arch...) est du code
# d'entrainement des phases precedentes, inutile ici.
COPY --from=builder /app/src/aspect_sentiment /app/src/aspect_sentiment

ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"
ENV OMP_NUM_THREADS=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", \
     "--host", "0.0.0.0", "--port", "8000"]
