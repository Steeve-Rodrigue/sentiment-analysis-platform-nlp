"""
src/multilingual/cross_lingual.py

Phase 8 -- Multilingue -- bloc "transfert zero-shot cross-lingue".

Repond directement a la problematique du projet (voir
plan-projet-globatrend-insights.md, section 1bis) : peut-on entrainer
UNIQUEMENT sur l'anglais et evaluer directement sur d'autres langues,
SANS AUCUN exemple etiquete dans ces langues ?

Theorie resumee (voir la conversation associee pour le detail) :

XLM-RoBERTa (XLM-R) est pre-entraine SIMULTANEMENT sur 100 langues,
partageant un espace de representation commun -- un mot espagnol et
son equivalent anglais finissent proches dans cet espace, meme sans
paire traduite explicite montree pendant le pre-entrainement.

Le transfert zero-shot consiste a fine-tuner XLM-R UNIQUEMENT sur des
donnees anglaises etiquetees (les plus abondantes), puis a l'evaluer
DIRECTEMENT sur d'autres langues -- le savoir "transfere" via l'espace
multilingue partage, sans jamais voir un seul exemple etiquete dans
la langue cible.

NOTE IMPORTANTE (verifiee empiriquement) : ce module necessite un
acces reseau a huggingface.co pour telecharger XLM-R -- bloque dans
l'environnement sandbox utilise pour ecrire ce code (meme situation
que DistilBERT en Phase 6). Reutilise l'infrastructure de
transformers_arch/fine_tuning.py (SentimentDataset, tokenize_dataset)
plutot que de la dupliquer.
"""

from __future__ import annotations

from transformers_arch.fine_tuning import (
    SentimentDataset,
    evaluate_fine_tuned_model,
    fine_tune_model,
    tokenize_dataset,
)


def load_xlmr_classifier(num_labels: int = 2):
    """Charge XLM-RoBERTa pre-entraine, avec une tete de classification
    neuve -- meme principe que load_pretrained_classifier() de la
    Phase 6, mais avec xlm-roberta-base (multilingue) plutot que
    distilbert-base-uncased (anglais seulement)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    id2label = {0: "negative", 1: "positive"}
    label2id = {"negative": 0, "positive": 1}

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    model = AutoModelForSequenceClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )
    return model, tokenizer


def fine_tune_on_source_language(
    model,
    tokenizer,
    source_texts: list[str],
    source_labels: list[int],
    eval_texts: list[str],
    eval_labels: list[int],
    epochs: int = 3,
):
    """Fine-tune XLM-R sur UNE SEULE langue source (typiquement
    l'anglais, la plus abondante). Reutilise fine_tune_model() de la
    Phase 6 -- meme mecanique, seul le modele de base change."""
    train_encodings = tokenize_dataset(source_texts, tokenizer)
    eval_encodings = tokenize_dataset(eval_texts, tokenizer)

    train_dataset = SentimentDataset(train_encodings, source_labels)
    eval_dataset = SentimentDataset(eval_encodings, eval_labels)

    return fine_tune_model(model, train_dataset, eval_dataset, epochs=epochs)


def evaluate_zero_shot(
    trainer, tokenizer, target_texts: list[str], target_labels: list[int]
) -> dict:
    """Evalue le modele (fine-tune UNIQUEMENT sur la langue source) sur
    une langue CIBLE jamais vue pendant l'entrainement -- c'est le
    coeur du test zero-shot cross-lingue. Retourne accuracy et f1 pour
    cette langue cible specifiquement."""
    target_encodings = tokenize_dataset(target_texts, tokenizer)
    target_dataset = SentimentDataset(target_encodings, target_labels)
    trainer.eval_dataset = target_dataset
    return evaluate_fine_tuned_model(trainer)


def compare_languages_zero_shot(
    trainer,
    tokenizer,
    language_test_sets: dict[str, tuple[list[str], list[int]]],
) -> dict[str, dict]:
    """Evalue le meme modele (fine-tune sur l'anglais uniquement) sur
    PLUSIEURS langues cibles a la fois. language_test_sets est un dict
    {code_langue: (textes, labels)}. Retourne les resultats par
    langue -- permet de voir directement si le transfert se degrade
    pour les langues moins proches de l'anglais (typiquement le
    hindi, langue la moins dotee en donnees de pre-entrainement)."""
    results = {}
    for lang_code, (texts, labels) in language_test_sets.items():
        results[lang_code] = evaluate_zero_shot(trainer, tokenizer, texts, labels)
    return results


def fine_tune_on_multiple_languages(
    model,
    tokenizer,
    language_train_sets: dict[str, tuple[list[str], list[int]]],
    eval_texts: list[str],
    eval_labels: list[int],
    epochs: int = 3,
):
    """Fine-tune XLM-R sur un MELANGE de plusieurs langues a la fois --
    contrairement a fine_tune_on_source_language() (anglais seul), ce
    modele voit de VRAIS exemples natifs de chaque langue pendant
    l'entrainement, pas seulement un transfert indirect via l'espace
    partage. language_train_sets : dict {code_langue: (textes, labels)},
    fusionnes en un seul jeu d'entrainement melange."""
    all_texts: list[str] = []
    all_labels: list[int] = []
    for _, (texts, labels) in language_train_sets.items():
        all_texts.extend(texts)
        all_labels.extend(labels)

    return fine_tune_on_source_language(
        model,
        tokenizer,
        all_texts,
        all_labels,
        eval_texts,
        eval_labels,
        epochs=epochs,
    )
