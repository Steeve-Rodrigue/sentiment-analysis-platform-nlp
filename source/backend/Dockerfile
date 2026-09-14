# source/backend/Dockerfile
#
# Image de l'API FastAPI. Build depuis la RACINE du repo (contexte),
# car l'app depend a la fois de source/backend/app et de src/ (modeles
# ML, phases 1-9) -- un seul pyproject.toml/uv.lock pour tout le repo.
#
#   docker build -f source/backend/Dockerfile -t globatrend-backend .
#   docker compose build backend

FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

# Dependances -- couche cachee separement du code applicatif.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Corpora NLTK utilises par l'extraction d'aspects (extract_aspect_candidates,
# Phase 9) -- pas de reseau requis a l'execution une fois l'image construite.
RUN uv run python -m nltk.downloader punkt_tab averaged_perceptron_tagger_eng

# Modeles Hugging Face utilises par model_registry.py -- pre-telecharges
# a la construction de l'image pour la meme raison que les corpora NLTK
# ci-dessus : pas de reseau requis a l'execution. HF_HUB_DISABLE_XET=1
# evite l'erreur "xet-read-token" rencontree avec le backend de
# telechargement xet dans cet environnement Docker.
ENV HF_HUB_DISABLE_XET=1
RUN uv run python -c "\
from transformers import AutoModelForSequenceClassification, AutoTokenizer; \
AutoTokenizer.from_pretrained('Steeve2ml/globatrend-sentiment-distilbert'); \
AutoModelForSequenceClassification.from_pretrained('Steeve2ml/globatrend-sentiment-distilbert');\
AutoModelForSequenceClassification.from_pretrained('Steeve2ml/globatrend-absa-english-classifier'); \
AutoTokenizer.from_pretrained('distilbert-base-uncased')"

# Dataset SemEval ABSA utilise par load_semeval_absa() (Phase 9) pour
# alimenter le simulateur de producteur Kafka -- pre-telecharge ici
# pour la meme raison que les modeles ci-dessus : sans cette ligne, le
# dataset n'est jamais mis en cache et load_semeval_absa() echoue au
# demarrage une fois HF_HUB_OFFLINE=1 applique plus bas (repli silencieux
# sur 10 avis fixes dans producer_simulator.py).
RUN uv run python -c "\
from datasets import load_dataset; \
load_dataset('tomaarsen/setfit-absa-semeval-restaurants')"

# Une fois les modeles en cache dans l'image, interdit tout appel
# reseau au demarrage du conteneur (voir model_registry.py::load_all).
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Code applicatif : src/ (phases ML) + source/backend/app (API).
COPY src/ ./src/
COPY source/backend/app ./source/backend/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "source/backend"]
