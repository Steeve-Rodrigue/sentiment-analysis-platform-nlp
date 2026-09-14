"""
tests/multilingual/test_translation.py

Tests unitaires pour src/multilingual/translation.py.
Necessitent un acces reseau (telechargement des modeles MarianMT et
DistilBERT) -- marques @pytest.mark.network.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from multilingual.translation import TRANSLATION_MODELS


def test_translation_models_cover_project_languages():
    # aucun reseau necessaire -- juste verifier le dict de config
    assert set(TRANSLATION_MODELS.keys()) == {"es", "de", "fr", "hi"}


def test_unsupported_language_raises_value_error():
    from multilingual.translation import translate_to_english

    with pytest.raises(ValueError):
        translate_to_english("some text", "ja")  # japonais, pas supporte


@pytest.mark.network
def test_translate_to_english_french():
    from multilingual.translation import translate_to_english

    resultat = translate_to_english("La livraison etait tres rapide", "fr")
    assert "delivery" in resultat.lower() or "fast" in resultat.lower()


@pytest.mark.network
def test_classify_via_translation_full_pipeline():
    from multilingual.translation import classify_via_translation
    from transformers_arch.fine_tuning import load_pretrained_classifier

    model, tokenizer = load_pretrained_classifier()
    resultat = classify_via_translation(
        "Ce produit est absolument fantastique", "fr", model, tokenizer
    )
    assert "translated_text" in resultat
    assert "predicted_label" in resultat
    assert resultat["predicted_label"] in ["positive", "negative"]
