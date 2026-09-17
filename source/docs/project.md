- slug: "financeiq"
  title: "FinanceIQ : Suivi de factures piloté par des agents IA"
  properties: "Application de suivi de factures où un système d'agents extrait,
    catégorise et vérifie chaque document , en demandant confirmation à
    l'utilisateur quand il doute, plutôt que de deviner silencieusement."
  context:
    - type: text
      content: |
        Extraire des informations fiables d'une facture ou d'un ticket de caisse
        scanné est un problème trompeur : les caractères peuvent être parfaitement
        lisibles tout en ne correspondant à rien de réel; un nom d'entreprise mal
        identifié, un sous-total confondu avec un montant remis en espèces, une
        adresse dont l'ordre des mots ne veut rien dire. Les outils d'extraction
        classiques (OCR + modèle de langage texte) héritent de ces erreurs sans
        jamais les questionner.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363942/Capture_d_%C3%A9cran_du_2026-09-02_17-27-54_hpylvc.png"
    - type: image
      url : "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363941/Capture_d_%C3%A9cran_du_2026-09-02_17-29-11_mpce0h.png"
  problematic:
    - type: text
      content: |
        La plupart des outils de gestion de factures choisissent entre deux
        extrêmes : l'automatisation intégrale, qui insère silencieusement des
        valeurs fausses dans la base de données, ou la saisie manuelle intégrale,
        fastidieuse et qui n'exploite pas l'IA. Aucun des deux ne sait dire
        « je ne suis pas sûr, peux-tu confirmer ? »  ce qui est pourtant le
        comportement le plus utile face à un document ambigu.
  methodology:
    - type: text
      content: |
        Chaque agent , extracteur, catégoriseur  renvoie un triplet
        {résultat, confiance, raisonnement}. Confiance haute : le résultat
        est accepté. Confiance moyenne : l'agent réessaie avec une approche
        différente (modèle plus puissant, historique du fournisseur). Toujours
        incertain après relance : le système crée une question adressée à
        l'utilisateur au lieu de deviner.
    - type: text
      content: |
        Le tableau de bord se décline en plusieurs onglets , chacun pensé pour
        répondre à une question précise. Les données presentées ont été extraites de factures réelles, mais anonymisées pour la démo.
    - type: image
      url : "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363940/Capture_d_%C3%A9cran_du_2026-09-02_17-36-17_z10fu0.png"
    - type: text
      content: |
        OVERVIEW: Vue d'ensemble : dépenses du mois, nombre de factures
        traitées, taux de résolution automatique et questions en attente.
        Trois graphiques fixes (tendance sur 6 mois, top vendeurs, répartition
        par catégorie) et les derniers uploads pour un état des lieux immédiat.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788386820/Capture_d_%C3%A9cran_du_2026-09-02_17-35-46_hstfml.png"
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788386881/Capture_d_%C3%A9cran_du_2026-09-02_17-33-31_euuybh.png"
    - type: text
      content: |
        SPEND ANALYTICS: Exploration financière en profondeur avec filtres
        (période, granularité, vendeur, catégorie). Tendances, heatmap des
        dépenses par jour, distribution des montants, détection des abonnements
        récurrents et des factures anormalement élevées par rapport à la moyenne
        du fournisseur.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363941/Capture_d_%C3%A9cran_du_2026-09-02_17-31-08_er3ndl.png"
    - type: text
      content: |
        CATEGORIES: Suivi des catégories de dépenses : répartition,
        évolution mensuelle, taux de factures non catégorisées.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363941/Capture_d_%C3%A9cran_du_2026-09-02_17-34-28_cusqub.png"
    - type: text
      content: |
        VENDORS: Analyse par fournisseur : top vendeurs par montant et
        fréquence, nouveaux fournisseurs détectés, concentration des dépenses
        sur les trois premiers, et vue détaillée par vendeur avec historique
        complet de facturation.
    - type: image
      url: ""
    - type: text
      content: |
        ELICITATIONS: Suivi des questions posées à l'utilisateur :
        en attente, répondues, expirées, taux par étape du pipeline. La section
        du bas permet de répondre directement aux questions en attente sans
        changer de page.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363941/Capture_d_%C3%A9cran_du_2026-09-02_17-35-01_wslgrd.png"
    - type: text
      content: |
        LINE ITEMS: Analyse au niveau produit : articles les plus achetés,
        évolution du prix unitaire dans le temps pour un même produit, et taux
        de couverture de la catégorisation des lignes.
    - type: image
      url: "https://res.cloudinary.com/dp9qlaych/image/upload/v1788363940/Capture_d_%C3%A9cran_du_2026-09-02_17-35-21_bbgjhu.png"
  results_impact: |
    Application complète : authentification, sécurité multi-tenant (RLS),
    boucle agentique confiance → relance → élicitation, extraction par vision,
    catégorisation, tableau de bord 8 pages et mode démo public exécutant le
     pipeline IA sur de vraies factures.
  metrics:
    saisie_manuelle_par_facture: "4 à 6 minutes"
    financeiq_par_facture: "quelques secondes"
    bilan_mensuel_manuellement: "2 heures pour 40 factures"
    bilan_mensuel_financeiq: "5 minutes pour 40 factures"
    erreurs_saisie_manuelle: "20 à 25%"
    erreurs_financeiq: "moins de 9%"
  tech_stack:
    - Python 3.11+
    - FastAPI
    - SQLAlchemy
    - Alembic
    - openai sdk
    - PostgreSQL
    - OpenRouter
    - Next.js
    - React
    - TypeScript
    - Tailwind CSS
    - ECharts
    - Docker Compose
    - Render
    - Neon
  categories:
    - Data Engineering
    - Data Visualisation
    - IA Agentique
  github_url: "https://github.com/Steeve-Rodrigue/finance_iq"
  demo_url: "https://finance-iq-v1.vercel.app/"
  featured: false   # pas fait en groupe
  thumbnail_url: ""
  display_order: 1

#########################################################
