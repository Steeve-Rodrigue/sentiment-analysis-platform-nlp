"""
src/aspect_sentiment/absa.py

Phase 9 -- ABSA (produit central du projet).

Theorie resumee (voir la conversation associee pour le detail) :

Deux architectures possibles pour l'ABSA :
1. PIPELINE : extraction d'aspects (etape separee) PUIS classification
   du sentiment pour chaque aspect trouve.
2. JOINTE (retenue ici) : reformule le probleme comme une
   classification de PAIRE DE PHRASES -- (texte, aspect_candidat) ->
   sentiment. Meme mecanisme technique que DistilBERT (Phase 6), mais
   avec une entree a deux segments au lieu d'un seul.

L'EXTRACTION D'ASPECTS reutilise extract_noun_phrases() de la Phase 1
(preprocessing/linguistic.py) -- verifie empiriquement sur un avis
multi-aspects reel : les 3 aspects reels ("delivery", "product
quality", "Customer service") sont correctement identifies sans aucun
entrainement dedie, juste par grammaire (POS tagging). Cette baseline
sert de premiere etape avant la classification proprement dite.

La TOKENISATION EN PAIRE (texte, aspect) suit la convention standard
des Transformers : tokenizer(texte, aspect) insere automatiquement
[CLS] texte [SEP] aspect [SEP], avec des token_type_ids distinguant
les deux segments -- le modele apprend a lire "sachant que je me
concentre sur CET aspect precis, quel est le sentiment ?"

Necessite un acces reseau a huggingface.co (meme situation que
DistilBERT en Phase 6, XLM-R en Phase 8) -- bloque dans le sandbox
utilise pour ecrire ce code.
"""

from __future__ import annotations

from transformers_arch.fine_tuning import (
    evaluate_fine_tuned_model,
    fine_tune_model,
)

ASPECT_CATEGORIES = [
    "price",
    "delivery",
    "customer_service",
    "packaging",
    "product_quality",
    "website",
    "refund",
    "shipping",
    "warranty",
]


def load_semeval_absa(
    dataset_name: str = "tomaarsen/setfit-absa-semeval-restaurants",
    test_size: float = 0.2,
    random_state: int = 42,
):
    """Charge un vrai dataset ABSA (SemEval), le convertit en triples
    (texte, aspect, label). Utilise les VRAIS splits train/test du
    dataset (confirme via la documentation officielle Hugging Face :
    dataset["train"] et dataset["test"] existent tous les deux pour
    tomaarsen/setfit-absa-semeval-restaurants), avec repli sur un
    decoupage manuel si un seul split existe (autres datasets ABSA du
    Hub qui ne fourniraient qu'un split "train").

    Schema confirme (doc officielle SetFit ABSA) : colonnes text
    (phrase complete), span (l'aspect, peut faire plusieurs mots),
    label OU polarity selon la version du dataset (le sentiment pour
    CET aspect precis), ordinal (index si l'aspect apparait plusieurs
    fois dans le texte, non utilise ici).

    Remplace le jeu jouet de 10 phrases repetees (voir
    absa_experiments.txt) qui, verifie empiriquement, menait le modele
    a un raccourci (mot d'aspect -> etiquette fixe) plutot qu'a une
    vraie lecture du contexte.

    Retourne (train_textes, train_aspects, train_labels,
    eval_textes, eval_aspects, eval_labels)."""
    from datasets import load_dataset
    from sklearn.model_selection import train_test_split

    # "conflict" est la 4eme categorie officielle de SemEval-2014 ABSA
    # (un aspect mentionne A LA FOIS positivement et negativement dans
    # la meme phrase) -- omise par erreur dans une premiere version de
    # ce mapping, ce qui rejetait TOUTE ligne "conflict" (label=None).
    # Mappee ici sur "neutral" (choix defendable : ni franchement
    # positif ni franchement negatif), a documenter si utilisee dans
    # une publication du modele.
    label_map = {
        "negative": 0,
        "neutral": 1,
        "positive": 2,
        "conflict": 1,
    }

    def _extract_triples(ds, split_name: str = "") -> tuple[list, list, list]:
        texts, aspects, labels = [], [], []
        raisons_rejet = {"text": 0, "aspect": 0, "label": 0}
        labels_bruts_vus = set()

        for row in ds:
            text = row.get("text")
            aspect = row.get("span") or row.get("aspect")
            raw_label = row.get("label")
            if raw_label is None:
                raw_label = row.get("polarity")
            if raw_label is not None:
                labels_bruts_vus.add(raw_label)

            label = (
                label_map.get(raw_label.lower())
                if isinstance(raw_label, str)
                else raw_label
            )

            if not text:
                raisons_rejet["text"] += 1
                continue
            if not aspect:
                raisons_rejet["aspect"] += 1
                continue
            if label is None:
                raisons_rejet["label"] += 1
                continue

            texts.append(text)
            aspects.append(aspect)
            labels.append(label)

        if len(texts) == 0 and len(ds) > 0:
            print(
                f"ATTENTION [{split_name}] : 0 exemple extrait sur "
                f"{len(ds)} lignes brutes. Raisons de rejet : "
                f"{raisons_rejet}"
            )
            print(
                f"  Valeurs brutes de label/polarity rencontrees : {labels_bruts_vus}"
            )
            print(f"  Exemple de ligne brute : {ds[0]}")

        return texts, aspects, labels

    full_dataset = load_dataset(dataset_name)
    print(f"Splits disponibles : {list(full_dataset.keys())}")

    if "test" in full_dataset:
        # cas confirme pour tomaarsen/setfit-absa-semeval-restaurants :
        # utilise les VRAIS splits du dataset, pas un decoupage maison
        print("Utilisation des splits natifs train/test du dataset")
        train_ds = full_dataset["train"]
        eval_ds = full_dataset["test"]
        print(
            f"Colonnes : {train_ds.column_names}  |  "
            f"{len(train_ds)} lignes train, {len(eval_ds)} lignes test"
        )

        train_texts, train_aspects, train_labels = _extract_triples(
            train_ds, split_name="train"
        )
        eval_texts, eval_aspects, eval_labels = _extract_triples(
            eval_ds, split_name="test"
        )

        # CAS REEL RENCONTRE : le split "test" existe bien, mais sa
        # colonne label est VIDE ('') sur TOUTES les lignes -- pas une
        # erreur d'extraction, une vraie caracteristique de cette
        # version du dataset (probablement pensee pour une autre
        # sous-tache que la classification de polarite). Se rabat sur
        # un decoupage manuel du train plutot que de se fier
        # aveuglement a l'existence nominale d'un split "test".
        if len(eval_texts) == 0:
            print(
                "ATTENTION : le split 'test' officiel n'a aucune "
                "etiquette de polarite exploitable -- repli sur un "
                "decoupage manuel du split 'train' a la place."
            )
            idx = list(range(len(train_texts)))
            idx_train, idx_eval = train_test_split(
                idx, test_size=test_size, random_state=random_state
            )

            def _select(items, indices):
                return [items[i] for i in indices]

            all_texts = train_texts
            all_aspects = train_aspects
            all_labels = train_labels
            train_texts = _select(all_texts, idx_train)
            train_aspects = _select(all_aspects, idx_train)
            train_labels = _select(all_labels, idx_train)
            eval_texts = _select(all_texts, idx_eval)
            eval_aspects = _select(all_aspects, idx_eval)
            eval_labels = _select(all_labels, idx_eval)
    else:
        # repli : un seul split disponible, decoupage manuel
        print("Un seul split trouve -- decoupage manuel 80/20")
        ds = full_dataset["train"]
        print(f"Colonnes : {ds.column_names}  |  {len(ds)} lignes brutes")

        texts, aspects, labels = _extract_triples(ds, split_name="train")
        idx = list(range(len(texts)))
        idx_train, idx_eval = train_test_split(
            idx, test_size=test_size, random_state=random_state
        )

        def _select(items, indices):
            return [items[i] for i in indices]

        train_texts = _select(texts, idx_train)
        train_aspects = _select(aspects, idx_train)
        train_labels = _select(labels, idx_train)
        eval_texts = _select(texts, idx_eval)
        eval_aspects = _select(aspects, idx_eval)
        eval_labels = _select(labels, idx_eval)

    print(f"{len(train_texts)} exemples train, {len(eval_texts)} exemples eval")

    return (
        train_texts,
        train_aspects,
        train_labels,
        eval_texts,
        eval_aspects,
        eval_labels,
    )


# --- ABSA MULTILINGUE : transfert ZERO-SHOT (methode de la Phase 8) ---
#
# CORRECTION IMPORTANTE : une premiere version de ce module chargeait
# distilbert-base-uncased pour l'ABSA multilingue -- une ERREUR de
# fond, puisque ce modele n'est PAS multilingue, le transfert zero-shot
# ne peut structurellement pas fonctionner avec lui, quelles que soient
# les donnees. De plus, aucune source de donnees ABSA etiquetees
# accessible programmatiquement n'a ete trouvee pour l'espagnol/francais
# (les donnees officielles SemEval-2016 ES/FR necessitent une inscription
# manuelle sur metashare.ilsp.gr, pas un simple load_dataset()).
#
# LA VRAIE SOLUTION, alignee sur la problematique du projet (voir
# plan-projet-globatrend-insights.md, section 1bis) : entrainer UNE
# SEULE FOIS sur l'anglais (donnees SemEval reelles, deja disponibles),
# avec un modele MULTILINGUE (XLM-R, comme en Phase 8), puis evaluer en
# ZERO-SHOT sur de petits jeux de test traduits a la main -- pas besoin
# de donnees d'entrainement etiquetees dans chaque langue.


def load_multilingual_absa_classifier(num_labels: int = 3):
    """Charge XLM-RoBERTa (multilingue) avec une tete de classification
    ABSA -- PAS distilbert-base-uncased (anglais seulement), qui ne
    permettrait structurellement aucun transfert zero-shot vers
    d'autres langues."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    id2label = {0: "negative", 1: "neutral", 2: "positive"}
    label2id = {"negative": 0, "neutral": 1, "positive": 2}

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    model = AutoModelForSequenceClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )
    return model, tokenizer


# Petits jeux de test ABSA multilingues, traduits a la main -- meme
# demarche que cross_lingual_experiments.txt (Phase 8). Format :
# (texte, aspect, label) par langue. Suffisant pour un premier signal
# de transfert zero-shot, PAS un vrai benchmark (echantillon trop
# petit) -- a etoffer avec de vraies donnees si l'on souhaite des
# chiffres publiables.
MULTILINGUAL_ABSA_TEST_SETS: dict[str, list[tuple[str, str, int]]] = {
    "es": [
        ("La entrega fue muy lenta pero el producto es excelente", "entrega", 0),
        ("La entrega fue muy lenta pero el producto es excelente", "producto", 2),
        ("El servicio al cliente fue muy amable y rapido", "servicio al cliente", 2),
    ],
    "de": [
        (
            "Die Lieferung war langsam, aber das Produkt ist ausgezeichnet",
            "Lieferung",
            0,
        ),
        ("Die Lieferung war langsam, aber das Produkt ist ausgezeichnet", "Produkt", 2),
        ("Der Kundendienst war sehr freundlich und schnell", "Kundendienst", 2),
    ],
    "fr": [
        ("La livraison etait lente mais le produit est excellent", "livraison", 0),
        ("La livraison etait lente mais le produit est excellent", "produit", 2),
        ("Le service client etait tres aimable et rapide", "service client", 2),
    ],
    "hi": [
        ("डिलीवरी धीमी थी लेकिन उत्पाद उत्कृष्ट है", "डिलीवरी", 0),
        ("डिलीवरी धीमी थी लेकिन उत्पाद उत्कृष्ट है", "उत्पाद", 2),
    ],
}


def evaluate_multilingual_zero_shot(trainer, tokenizer) -> dict:
    """Evalue un modele ABSA (fine-tune UNIQUEMENT sur l'anglais) en
    zero-shot sur les jeux de test multilingues traduits a la main --
    reutilise evaluate_fine_tuned_model() de la Phase 6, avec un
    eval_dataset different par langue a chaque appel. Retourne
    {code_langue: {accuracy, f1}}."""
    results = {}
    for lang, triples in MULTILINGUAL_ABSA_TEST_SETS.items():
        texts = [t for t, a, lab in triples]
        aspects = [a for t, a, lab in triples]
        labels = [lab for t, a, lab in triples]

        encodings = tokenize_aspect_pairs(texts, aspects, tokenizer)
        eval_dataset = AspectPairDataset(encodings, labels)
        trainer.eval_dataset = eval_dataset
        results[lang] = evaluate_fine_tuned_model(trainer)
    return results


# Noms generiques/abstraits frequemment extraits a tort comme aspects
# par la baseline grammaticale -- verifie empiriquement sur un avis
# reel : "this time" et "needs improvement" produisaient les faux
# aspects "time" et "improvement" (tous deux grammaticalement NN, donc
# indiscernables d'un vrai aspect par la seule grammaire). Cette liste
# filtre les candidats D'UN SEUL MOT correspondant a un nom generique
# -- les phrases multi-mots ("customer service") ne sont JAMAIS
# filtrees, seuls les mots isoles trop vagues pour etre un aspect
# produit/service reel.
GENERIC_NOUN_STOPWORDS = {
    "time",
    "improvement",
    "way",
    "thing",
    "things",
    "part",
    "bit",
    "lot",
    "point",
    "case",
    "kind",
    "sort",
    "moment",
    "matter",
    "everything",
    "anything",
    "something",
    "nothing",
}


def extract_aspect_candidates(text: str) -> list[str]:
    """Extrait des aspects candidats via la baseline grammaticale de
    la Phase 1 (groupes nominaux consecutifs), puis filtre les noms
    generiques isoles (voir GENERIC_NOUN_STOPWORDS) qui ne sont
    presque jamais de vrais aspects produit/service. Premiere etape
    de l'architecture pipeline -- reste une heuristique imparfaite,
    pas une extraction semantique veritable."""
    from nltk import pos_tag, word_tokenize

    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)

    phrases: list[str] = []
    current: list[str] = []
    for word, tag in tagged:
        if tag.startswith("NN"):
            current.append(word)
        else:
            if current:
                _add_if_not_generic(phrases, current)
                current = []
    if current:
        _add_if_not_generic(phrases, current)
    return phrases


def _add_if_not_generic(phrases: list[str], current: list[str]) -> None:
    """Ajoute la phrase candidate, sauf si c'est un SEUL mot generique
    (les phrases multi-mots ne sont jamais filtrees)."""
    is_single_generic = (
        len(current) == 1 and current[0].lower() in GENERIC_NOUN_STOPWORDS
    )
    if not is_single_generic:
        phrases.append(" ".join(current))


class AspectPairDataset:
    """Wrapper au format attendu par le Trainer de Hugging Face pour
    des paires (texte, aspect) -- meme principe que SentimentDataset
    de la Phase 6, mais chaque exemple encode DEUX segments."""

    def __init__(self, encodings, labels: list[int]):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx: int) -> dict:
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item

    def __len__(self) -> int:
        return len(self.labels)


def tokenize_aspect_pairs(
    texts: list[str],
    aspects: list[str],
    tokenizer,
    max_length: int = 256,
):
    """Tokenise des paires (texte, aspect) -- le tokenizer insere
    automatiquement [SEP] entre les deux segments et produit des
    token_type_ids qui les distinguent. texts et aspects doivent
    avoir la meme longueur (un aspect par texte)."""
    return tokenizer(
        texts,
        aspects,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    )


def load_absa_classifier(num_labels: int = 3):
    """Charge DistilBERT avec une tete de classification pour l'ABSA
    -- 3 classes par defaut (positive/negative/neutral), contre 2 pour
    le sentiment global de la Phase 6 (pas de neutre)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    id2label = {0: "negative", 1: "neutral", 2: "positive"}
    label2id = {"negative": 0, "neutral": 1, "positive": 2}

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )
    return model, tokenizer


def train_absa_model(
    model,
    tokenizer,
    train_texts: list[str],
    train_aspects: list[str],
    train_labels: list[int],
    eval_texts: list[str],
    eval_aspects: list[str],
    eval_labels: list[int],
    epochs: int = 3,
):
    """Fine-tune le modele ABSA sur des paires (texte, aspect, label).
    Reutilise fine_tune_model() de la Phase 6 -- seule la tokenisation
    en paire change par rapport a un fine-tuning de sentiment global."""
    train_encodings = tokenize_aspect_pairs(train_texts, train_aspects, tokenizer)
    eval_encodings = tokenize_aspect_pairs(eval_texts, eval_aspects, tokenizer)

    train_dataset = AspectPairDataset(train_encodings, train_labels)
    eval_dataset = AspectPairDataset(eval_encodings, eval_labels)

    return fine_tune_model(model, train_dataset, eval_dataset, epochs=epochs)


def predict_aspect_sentiment(
    text: str, aspects: list[str], model, tokenizer
) -> dict[str, str]:
    """Pipeline complet pour UN avis : pour chaque aspect candidat
    fourni, predit son sentiment individuellement -- c'est cette
    fonction qui produit la sortie finale attendue par le projet :
    {aspect: sentiment} plutot qu'un score de sentiment global unique."""
    import torch

    results = {}
    for aspect in aspects:
        inputs = tokenize_aspect_pairs([text], [aspect], tokenizer)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_class = torch.argmax(logits, dim=-1).item()
        results[aspect] = model.config.id2label[predicted_class]
    return results


def predict_aspect_sentiment_with_confidence(
    text: str, aspects: list[str], model, tokenizer
) -> dict[str, tuple[str, float]]:
    """Comme predict_aspect_sentiment(), mais renvoie aussi la
    confiance (probabilite softmax de la classe predite) pour chaque
    aspect -- {aspect: (sentiment, confidence)}. Fonction separee
    plutot que de changer la signature de predict_aspect_sentiment()
    pour ne pas casser ses appelants existants (pipeline Kafka,
    tests)."""
    import torch

    results = {}
    for aspect in aspects:
        inputs = tokenize_aspect_pairs([text], [aspect], tokenizer)
        with torch.no_grad():
            logits = model(**inputs).logits
        probabilities = torch.softmax(logits, dim=-1)
        predicted_class = torch.argmax(logits, dim=-1).item()
        label = model.config.id2label[predicted_class]
        confidence = probabilities[0, predicted_class].item()
        results[aspect] = (label, confidence)
    return results
