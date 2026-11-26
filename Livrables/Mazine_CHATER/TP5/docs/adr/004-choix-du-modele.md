# ADR 004 — Suivi des entraînements et version des données

## Contexte

Les entraînements précédents laissaient seulement `metrics.json`. Impossible
de savoir quel réglage avait produit quel résultat, ni sur quelle version du
CSV. Comparer deux essais demandait de tout relancer à la main.

## Décision

- Enregistrer chaque entraînement dans MLflow via `maintai/tracking.py`.
- Versionner le CSV avec DVC, en gardant un fichier `.dvc` dans Git.
- Continuer à écrire les artefacts locaux (`model.joblib`, `model_info.json`,
  `metrics.json`).

## Pourquoi

- MLflow donne un tableau comparatif des runs et recharge un modèle donné.
- L'empreinte MD5 commune à MLflow et DVC relie un run à une version précise
  des données.
- Les artefacts locaux restent la source utilisée par l'API : le suivi est
  un outil d'analyse, pas une dépendance en production.

## Conséquences

- `mlflow.db` et `mlruns/` doivent être ignorés par Git.
- Le fichier `data/sensors.csv` est ignoré par Git et récupéré par
  `dvc checkout` / `dvc pull`.
- Une personne qui clone le dépôt doit lancer `dvc pull` avant d'entraîner.

## Alternatives écartées

- **Nommer les fichiers à la main** (`metrics_v2_final.json`) : vite
  ingérable et sans lien fiable avec les données.
- **Tout mettre dans Git** : historique lourd et diffs binaires inutiles.
- **Un simple tableur** : pas de rechargement du modèle ni d'empreinte des
  données.
