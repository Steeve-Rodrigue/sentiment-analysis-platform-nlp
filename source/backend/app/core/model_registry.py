"""
source/backend/app/core/model_registry.py

Singleton charge UNE SEULE FOIS au demarrage du serveur -- evite de
recharger les modeles a chaque requete. Charge maintenant DEUX
modeles distincts : le sentiment global (DistilBERT, Phase 6) et
l'ABSA (Phase 9), pour les deux sections separees de la page
principale.
"""

from __future__ import annotations


class ModelRegistry:
    """Conteneur pour tous les modeles charges en memoire."""

    def __init__(self):
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self.absa_model = None
        self.absa_tokenizer = None
        self._loaded = False

    def load_all(self) -> None:
        """Charge tous les modeles necessaires. Appele UNE FOIS au
        demarrage (lifespan de FastAPI, main.py).

        IMPORTANT : charge le modele FINE-TUNE publie sur Hugging Face
        (Phase 6), PAS load_pretrained_classifier() seul -- celui-ci
        chargerait distilbert-base-uncased BRUT, avec une tete de
        classification JAMAIS ENTRAINEE (poids initialises au hasard).
        Bug reel rencontre en testant : /api/sentiment renvoyait une
        prediction quasi CONSTANTE (toujours "negative"), meme sur des
        avis clairement positifs -- le modele n'avait jamais appris
        quoi que ce soit sur le sentiment."""
        if self._loaded:
            return

        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        sentiment_repo = "Steeve2ml/globatrend-sentiment-distilbert"
        absa_repo = "Steeve2ml/globatrend-absa-english-classifier"
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_repo)
        # NOTE : le tokenizer publie sur absa_repo est casse (fichiers
        # XLMRobertaTokenizer alors que le modele est un DistilBERT,
        # vocab_size 30522) -- charger ce tokenizer produit des
        # input_ids hors des bornes de la table d'embeddings du modele
        # (IndexError a l'inference). Le modele ABSA est fine-tune a
        # partir de distilbert-base-uncased (meme vocab_size 30522,
        # confirme) : on charge donc son tokenizer depuis la base,
        # jamais depuis absa_repo.
        self.absa_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            sentiment_repo
        )

        self.absa_model = AutoModelForSequenceClassification.from_pretrained(absa_repo)

        self._loaded = True

    def is_ready(self) -> bool:
        return self._loaded


registry = ModelRegistry()
