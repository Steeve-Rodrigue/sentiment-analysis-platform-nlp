"""
source/backend/prefetch_review_pool.py

Pre-telecharge le dataset SemEval ABSA et sauvegarde la liste
dedupliquee des avis dans un fichier JSON statique -- a executer UNE
SEULE FOIS au BUILD de l'image Docker (meme logique que
export_and_quantize_models.py), jamais au runtime.

POURQUOI : app/services/producer_simulator.py appelait avant
`datasets.load_dataset(...)` + scikit-learn EN DIRECT au demarrage du
serveur pour piocher des avis reels dans le pool -- mais ni `datasets`
ni `scikit-learn` ne sont installes au runtime (image finale
torch-free, voir model_registry.py/export_and_quantize_models.py), et
le telechargement necessitait un acces reseau a huggingface.co a
chaque demarrage du conteneur. Prefetch au build : le runtime n'a
plus qu'a lire un JSON statique, aucune dependance ni reseau
necessaire.
"""

from __future__ import annotations

import json

OUTPUT_PATH = "review_pool.json"


def main() -> None:
    from aspect_sentiment.absa import load_semeval_absa

    (train_texts, _, _, eval_texts, _, _) = load_semeval_absa()
    # meme deduplication que l'ancien load_review_pool() -- un meme
    # avis peut apparaitre plusieurs fois dans le dataset brut (une
    # ligne par aspect detecte dans cet avis).
    reviews = list(dict.fromkeys(train_texts + eval_texts))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    print(f"{len(reviews)} avis SemEval sauvegardes dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
