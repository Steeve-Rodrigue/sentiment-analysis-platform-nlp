"""
source/backend/export_and_quantize_models.py

Exporte les 2 modeles (sentiment, ABSA) en ONNX PUIS les quantifie en
int8 -- a executer UNE SEULE FOIS au BUILD de l'image Docker (comme
prefetch_models.py avant lui), jamais au runtime.

POURQUOI CE FICHIER EXISTE : sur Render (tier gratuit, 512 Mo de RAM),
PyTorch + Transformers + 2 modeles DistilBERT en fp32 depassent
largement le quota -- PyTorch a lui seul pese generalement 300-500 Mo
une fois importe, avant meme de charger un modele.

VERIFIE EMPIRIQUEMENT (sur un DistilBERT local, poids aleatoires,
architecture identique a nos modeles reels) :
  Poids PyTorch (fp32)      : 267.8 Mo
  ONNX (avant quantification): 267.7 Mo (conversion de format, pas de
                                gain de taille a cette etape)
  ONNX quantifie (int8)      : 67.1 Mo  -- REDUCTION DE 75%

Et surtout : l'inference sur le modele quantifie fonctionne SANS
IMPORTER TORCH au runtime, en utilisant return_tensors="np" (NumPy)
plutot que "pt" (PyTorch) -- verifie : les logits reviennent en
numpy.ndarray, pas torch.Tensor. C'est ce qui permet de retirer
`torch` des dependances de l'image FINALE (seul `onnxruntime`,
beaucoup plus leger, est necessaire au runtime).

Pour 2 modeles : ~536 Mo (PyTorch fp32) -> ~134 Mo (ONNX quantifie),
plus la disparition de PyTorch lui-meme du runtime -- la combinaison
qui doit faire rentrer le conteneur dans 512 Mo.

IMPORTANT : export fait via torch.onnx.export() + onnxruntime.quantization
DIRECTEMENT, pas via `optimum` -- verifie empiriquement que `optimum`
(toutes versions >=1.24.0 disponibles) exige `transformers<4.58.0` via
sa dependance `optimum-onnx`, incompatible avec `transformers[torch]>=5.14.1`
utilise par ce projet (et par les modeles publies, entraines avec
transformers 5.x). torch + onnxruntime seuls n'ont pas ce probleme.
"""

from __future__ import annotations

import os

import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Doit correspondre EXACTEMENT aux identifiants utilises dans
# model_registry.py -- sinon le cache pre-telecharge/exporte ne
# correspondra pas a ce que le code demande au runtime.
MODELS_TO_EXPORT = {
    "sentiment": "Steeve2ml/globatrend-sentiment-distilbert",
    "absa": "Steeve2ml/globatrend-absa-english-classifier",
}

# VERIFIE EMPIRIQUEMENT (a nouveau, au moment de cet export) : le
# tokenizer publie sur le repo ABSA est un XLMRobertaTokenizer
# (vocab_size 250002, sentencepiece) alors que le modele est un
# DistilBERT (vocab_size 30522, WordPiece) -- charger ce tokenizer
# produit des input_ids hors des bornes de la table d'embeddings du
# modele (IndexError/Gather out-of-bounds a l'inference ONNX). Le
# modele ABSA est fine-tune a partir de distilbert-base-uncased (meme
# vocab_size 30522) : on charge donc son tokenizer depuis la base,
# jamais depuis le repo ABSA.
TOKENIZER_OVERRIDES = {
    "absa": "distilbert-base-uncased",
    "sentiment": "Steeve2ml/globatrend-sentiment-distilbert",
}

OUTPUT_BASE_DIR = "onnx_models"


def export_and_quantize(
    repo_id: str, output_dir: str, tokenizer_repo_id: str | None = None
) -> None:
    print(f"\n=== {repo_id} ===")

    print("Chargement du modele PyTorch...")
    model = AutoModelForSequenceClassification.from_pretrained(repo_id)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_repo_id or repo_id)

    os.makedirs(output_dir, exist_ok=True)
    fp32_path = f"{output_dir}/model_fp32_tmp.onnx"
    quantized_path = f"{output_dir}/model_quantized.onnx"

    print("Export PyTorch -> ONNX...")
    # DistilBERT n'utilise pas token_type_ids (pas de token_type
    # embeddings dans l'architecture) -- input_ids + attention_mask
    # suffisent, meme pour l'ABSA (classification de paire (texte,
    # aspect), encodee par le tokenizer comme un seul segment
    # [CLS] texte [SEP] aspect [SEP]).
    dummy_inputs = tokenizer("dummy text", return_tensors="pt")
    torch.onnx.export(
        model,
        (dummy_inputs["input_ids"], dummy_inputs["attention_mask"]),
        fp32_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "logits": {0: "batch"},
        },
        opset_version=17,
        dynamo=False,  # exporteur TorchScript -- pas besoin d'onnxscript
    )

    print("Quantification dynamique (int8)...")
    quantize_dynamic(fp32_path, quantized_path, weight_type=QuantType.QInt8)
    os.remove(fp32_path)

    tokenizer.save_pretrained(output_dir)
    model.config.save_pretrained(output_dir)

    print(f"Modele quantifie sauvegarde dans : {output_dir}")


if __name__ == "__main__":
    for name, repo_id in MODELS_TO_EXPORT.items():
        export_and_quantize(
            repo_id, f"{OUTPUT_BASE_DIR}/{name}", TOKENIZER_OVERRIDES.get(name)
        )

    print("\nTous les modeles sont exportes et quantifies.")
