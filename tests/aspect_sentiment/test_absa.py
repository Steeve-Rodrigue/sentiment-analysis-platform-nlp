"""
tests/aspect_sentiment/test_absa.py

Tests unitaires pour src/aspect_sentiment/absa.py.

Sans reseau : extraction d'aspects (filtre inclus), AspectPairDataset.
Avec reseau (@pytest.mark.network) : tout ce qui charge un modele
(DistilBERT pour l'entrainement anglais, XLM-R pour le zero-shot
multilingue).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from aspect_sentiment.absa import (
    ASPECT_CATEGORIES,
    GENERIC_NOUN_STOPWORDS,
    MULTILINGUAL_ABSA_TEST_SETS,
    AspectPairDataset,
    extract_aspect_candidates,
)


def test_aspect_categories_match_project_scope():
    # rappel plan-projet-globatrend-insights.md : 9 aspects definis
    assert len(ASPECT_CATEGORIES) == 9
    assert "delivery" in ASPECT_CATEGORIES
    assert "product_quality" in ASPECT_CATEGORIES


def test_extract_aspect_candidates_finds_real_aspects():
    avis = "The delivery was slow but the product quality is excellent"
    aspects = extract_aspect_candidates(avis)
    assert "delivery" in aspects
    assert "product quality" in aspects


def test_extract_aspect_candidates_on_multi_aspect_review():
    avis = (
        "The delivery was slow but the product quality is excellent. "
        "Customer service was also very helpful."
    )
    aspects = extract_aspect_candidates(avis)
    assert len(aspects) >= 3


def test_generic_single_word_nouns_are_filtered_out():
    # regression du bug reel : "this time" et "needs improvement"
    # produisaient les faux aspects "time" et "improvement" (tous deux
    # grammaticalement NN, indiscernables d'un vrai aspect par la
    # seule grammaire) -- verifie sur la phrase exacte qui a revele
    # le probleme
    avis = (
        "The delivery was fast this time but customer service still "
        "needs improvement, though the price is fair"
    )
    aspects = extract_aspect_candidates(avis)
    assert "time" not in aspects
    assert "improvement" not in aspects
    assert "delivery" in aspects
    assert "customer service" in aspects
    assert "price" in aspects


def test_multi_word_phrases_are_never_filtered():
    # le filtre ne s'applique QU'AUX candidats d'un seul mot -- une
    # phrase multi-mots doit toujours passer, meme si elle contient un
    # mot par ailleurs generique
    assert "time" in GENERIC_NOUN_STOPWORDS
    avis = "The delivery time was reasonable"
    aspects = extract_aspect_candidates(avis)
    assert any("time" in a for a in aspects)


def test_aspect_pair_dataset_length():
    import torch

    encodings = {
        "input_ids": torch.tensor([[1, 2, 3], [4, 5, 6]]),
        "token_type_ids": torch.tensor([[0, 0, 1], [0, 0, 1]]),
    }
    dataset = AspectPairDataset(encodings, labels=[2, 0])
    assert len(dataset) == 2


def test_aspect_pair_dataset_getitem_returns_labeled_dict():
    import torch

    encodings = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "token_type_ids": torch.tensor([[0, 0, 1]]),
    }
    dataset = AspectPairDataset(encodings, labels=[2])
    item = dataset[0]
    assert item["labels"] == 2
    assert "token_type_ids" in item


def test_multilingual_test_sets_cover_all_four_target_languages():
    # sans reseau : verifie juste la structure des donnees de test
    assert set(MULTILINGUAL_ABSA_TEST_SETS.keys()) == {"es", "de", "fr", "hi"}
    for lang, triples in MULTILINGUAL_ABSA_TEST_SETS.items():
        assert len(triples) > 0
        for text, aspect, label in triples:
            assert label in [0, 1, 2]


@pytest.mark.network
def test_load_absa_classifier_downloads_distilbert():
    from aspect_sentiment.absa import load_absa_classifier

    model, tokenizer = load_absa_classifier()
    assert model.config.num_labels == 3


@pytest.mark.network
def test_load_semeval_absa_returns_six_way_split():
    from aspect_sentiment.absa import load_semeval_absa

    resultat = load_semeval_absa()
    assert len(resultat) == 6
    train_t, train_a, train_l, eval_t, eval_a, eval_l = resultat
    assert len(train_t) > 0
    assert len(eval_t) > 0
    assert len(train_t) == len(train_a) == len(train_l)


@pytest.mark.network
def test_predict_aspect_sentiment_returns_one_label_per_aspect():
    from aspect_sentiment.absa import (
        load_absa_classifier,
        predict_aspect_sentiment,
    )

    model, tokenizer = load_absa_classifier()
    avis = "The delivery was slow but the product quality is excellent"
    aspects = ["delivery", "product quality"]

    resultats = predict_aspect_sentiment(avis, aspects, model, tokenizer)
    assert set(resultats.keys()) == set(aspects)
    for label in resultats.values():
        assert label in ["negative", "neutral", "positive"]


@pytest.mark.network
def test_load_multilingual_absa_classifier_uses_xlmr():
    # regression de l'erreur de fond corrigee : le modele multilingue
    # DOIT etre XLM-R, pas distilbert-base-uncased (qui ne permettrait
    # structurellement aucun transfert zero-shot)
    from aspect_sentiment.absa import load_multilingual_absa_classifier

    model, tokenizer = load_multilingual_absa_classifier()
    assert "xlm-roberta" in tokenizer.name_or_path.lower()


@pytest.mark.network
def test_zero_shot_multilingual_flow_end_to_end():
    # test de bout en bout : fine-tune sur l'anglais SemEval reel,
    # evalue en zero-shot sur les 4 langues cibles, SANS AUCUN exemple
    # d'entrainement dans ces langues -- coeur de la problematique
    # du projet
    from aspect_sentiment.absa import (
        evaluate_multilingual_zero_shot,
        load_multilingual_absa_classifier,
        load_semeval_absa,
        train_absa_model,
    )

    (train_t, train_a, train_l, eval_t, eval_a, eval_l) = load_semeval_absa()

    # sous-echantillon pour un test rapide, pas le dataset complet
    model, tokenizer = load_multilingual_absa_classifier()
    trainer = train_absa_model(
        model,
        tokenizer,
        train_t[:100],
        train_a[:100],
        train_l[:100],
        eval_t[:20],
        eval_a[:20],
        eval_l[:20],
        epochs=1,
    )

    resultats = evaluate_multilingual_zero_shot(trainer, tokenizer)
    assert set(resultats.keys()) == {"es", "de", "fr", "hi"}
    for lang, res in resultats.items():
        assert "eval_accuracy" in res
        assert 0.0 <= res["eval_accuracy"] <= 1.0
