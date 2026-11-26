# ADR 000 : régression logistique pour la prédiction de panne

Date : 12/11/2026 · Auteur : Yahya Baid (G1My)

## Contexte

MaintAI doit estimer une probabilité de panne à partir de quatre relevés de capteurs (`temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours`) et déclencher une alerte si cette probabilité atteint un seuil. Le modèle doit rester simple à entraîner, à versionner et à servir derrière une API FastAPI, puis une interface Streamlit.

## Options étudiées

1. **Classifieur naïf (classe majoritaire)** : très simple, mais il ne détecte aucune panne (rappel à 0). Inutile pour une alerte de maintenance.
2. **Régression logistique + StandardScaler** : modèle linéaire, probabilités calibrées, pipeline unique (`joblib`), seuil de décision réglable (0,3). Interprétable et rapide.
3. **Forêt aléatoire / modèle plus complexe** : meilleur pouvoir prédictif possible, mais plus lourd à sauvegarder, plus difficile à expliquer en cours, et disproportionné pour un jeu synthétique de 5 000 lignes.

## Décision

Le pipeline `StandardScaler` + `LogisticRegression` est retenu. Le prétraitement fait partie du modèle sauvegardé, le seuil d'alerte est fixé à 0,3 (plutôt que 0,5) pour privilégier le rappel, et les métriques sont comparées à une baseline `DummyClassifier(most_frequent)`.

## Conséquences

- L'API charge un seul artefact `models/model.joblib` au démarrage.
- Le contrat d'entrée (`model_info.json`) fige l'ordre des variables.
- Un modèle plus expressif pourra remplacer le classifieur sans changer l'API ni Streamlit, tant que `predict_proba` reste disponible.
