"""
app/core/model_registry.py

Singleton charge UNE SEULE FOIS au demarrage du serveur -- charge
maintenant les modeles ONNX QUANTIFIES (voir
export_and_quantize_models.py, execute au BUILD de l'image Docker),
pas les modeles PyTorch bruts.

POURQUOI : sur Render (tier gratuit, 512 Mo de RAM), PyTorch +
Transformers + 2 modeles DistilBERT fp32 depassaient le quota.

IMPORTANT : on charge l'ONNX via onnxruntime.InferenceSession
DIRECTEMENT, pas via optimum.onnxruntime.ORTModelForSequenceClassification
-- verifie empiriquement que le package `optimum` (meme sans extra)
declare `torch` comme dependance INCONDITIONNELLE, ce qui aurait
reintroduit torch (+ un stack CUDA complet) dans l'image finale,
annulant tout le gain de cette migration. onnxruntime + AutoConfig
(pour id2label) + AutoTokenizer n'ont besoin ni l'un ni l'autre de
torch."""

from __future__ import annotations

from pathlib import Path

# Chemin ABSOLU, resolu par rapport a ce fichier -- pas relatif au
# repertoire de travail du processus. VERIFIE EMPIRIQUEMENT (Docker) :
# le conteneur demarre avec WORKDIR=/app mais onnx_models/ vit dans
# /app/backend (uvicorn --app-dir backend change seulement sys.path,
# pas le cwd) -- un chemin relatif "onnx_models/..." pointait donc
# vers /app/onnx_models (inexistant), et AutoTokenizer/AutoConfig
# retombaient sur un lookup Hugging Face Hub (401, le nom ressemblant
# a un repo_id). model_registry.py vit dans app/core/, onnx_models/ a
# la racine de source/backend/ (meme localement qu'en image finale
# Docker, ou model_registry.py est copie vers /app/backend/app/core/
# et onnx_models vers /app/backend/onnx_models) : deux niveaux plus
# haut que ce fichier.
ONNX_MODELS_DIR = Path(__file__).resolve().parents[2] / "onnx_models"


class ModelRegistry:
    """Conteneur pour tous les modeles charges en memoire."""

    def __init__(self):
        self.sentiment_session = None
        self.sentiment_tokenizer = None
        self.sentiment_config = None
        self.sentiment_input_names = None
        self.absa_session = None
        self.absa_tokenizer = None
        self.absa_config = None
        self.absa_input_names = None
        self._loaded = False

    def load_all(self) -> None:
        """Charge les modeles ONNX quantifies deja exportes au build
        (voir export_and_quantize_models.py) -- aucun telechargement,
        aucun import PyTorch necessaire ici."""
        if self._loaded:
            return

        import onnxruntime as ort
        from transformers import AutoConfig, AutoTokenizer

        sentiment_dir = ONNX_MODELS_DIR / "sentiment"
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained(str(sentiment_dir))
        self.sentiment_config = AutoConfig.from_pretrained(str(sentiment_dir))
        self.sentiment_session = ort.InferenceSession(
            str(sentiment_dir / "model_quantized.onnx")
        )
        # le tokenizer renvoie token_type_ids en plus de input_ids/
        # attention_mask, mais le graphe ONNX n'a ete exporte qu'avec
        # ces deux entrees (DistilBERT n'utilise pas token_type_ids) --
        # onnxruntime rejette toute cle absente du graphe, donc on ne
        # garde au runtime que ce que le graphe declare reellement.
        self.sentiment_input_names = {
            i.name for i in self.sentiment_session.get_inputs()
        }

        absa_dir = ONNX_MODELS_DIR / "absa"
        self.absa_tokenizer = AutoTokenizer.from_pretrained(str(absa_dir))
        self.absa_config = AutoConfig.from_pretrained(str(absa_dir))
        self.absa_session = ort.InferenceSession(str(absa_dir / "model_quantized.onnx"))
        self.absa_input_names = {i.name for i in self.absa_session.get_inputs()}

        self._loaded = True

    def is_ready(self) -> bool:
        return self._loaded


registry = ModelRegistry()
