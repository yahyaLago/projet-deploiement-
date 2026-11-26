# ADR 005 : le modèle par un volume, les données et les secrets hors de l'image Docker

Date : 26/11/2026 · Auteurs : Wenn BOUKA (dossier `tp/tp6/Wenn_BOUKA`)

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : l'API et l'interface sont livrées dans une image Docker `maintai:0.4.0`. Il faut décider ce qui entre dans cette image (partageable, reconstruite à chaque changement de code) et ce qui arrive au lancement, sachant que le modèle est réentraîné et versionné indépendamment du code (TP5, MLflow et DVC) et que la clé API est un secret.

## Options étudiées
1. **Modèle copié dans l'image** (`COPY models/ ./models`)
   - Avantages : une image autonome, un seul artefact à livrer ; impossible d'oublier le volume (pas de 503 « Modèle non chargé ») ; le couple code/modèle est figé et traçable par le tag de l'image.
   - Inconvénients : chaque réentraînement impose un rebuild et une nouvelle diffusion de l'image ; l'image grossit avec le modèle ; le modèle devient visible par toute personne qui récupère l'image ; le versionnement DVC du modèle est doublé par celui des images.
2. **Modèle monté par un volume en lecture seule** (`-v ./models:/app/models:ro`)
   - Avantages : on change de modèle sans toucher à l'image (redémarrage du conteneur) ; image plus légère et identique pour toutes les versions du modèle ; `:ro` empêche le conteneur de modifier le modèle ; cohérent avec DVC, qui reste la source de vérité du modèle.
   - Inconvénients : un oubli du volume donne une API qui démarre mais répond 503 (observé : `model_loaded:false`) ; le serveur doit disposer du dossier `models/` à côté de l'image ; il faut veiller à ce que la version de scikit-learn de l'image corresponde à celle qui a écrit le modèle (d'où `scikit-learn==1.8.0` figé).
3. **Données et secrets** : dans l'image, ou hors de l'image (volumes pour `data/`, `--env-file .env` / `env_file` pour la clé).
   - Dans l'image : un lancement plus simple, mais la clé serait publiée avec l'image (couches inspectables) et changer de clé ou de données imposerait un rebuild ; les données alourdiraient l'image.
   - Hors de l'image : un secret jamais diffusé et changeable sans rebuild, des données mises à jour indépendamment ; en contrepartie, chaque machine doit fournir son `.env` et son dossier `data/`.

## Décision
- **Option 2** : le modèle arrive par le volume `./models:/app/models:ro`, aussi bien avec `docker run` qu'avec le service `api` de `compose.yaml`. Raison principale : le modèle évolue au rythme des réentraînements (MLflow, DVC), pas du code ; le lier à l'image obligerait à reconstruire et rediffuser l'image à chaque nouveau modèle.
- Les **données** arrivent par `./data:/app/data:ro` (service `ui`) et la **clé API** par `env_file: .env`. L'image ne contient que Python, les bibliothèques figées de `requirements-docker.txt` et le code `maintai/` et `ui/`.
- **`.dockerignore`** garantit ce partage : il exclut du contexte de build `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/`, `.dvc/`, `.venv/`, les caches (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`), `.git/`, `tests/`, `docs/`, `web/` et les fichiers Markdown. Même une instruction `COPY . .` ajoutée par erreur ne pourrait pas y faire entrer un secret ou les données ; le contexte envoyé au moteur est aussi plus petit, donc le build plus rapide.

## Conséquences
- Facilite : remplacer le modèle par un simple redémarrage ; partager l'image sans risque de fuite de la clé ou des données ; des builds rapides grâce au cache (les bibliothèques avant le code).
- Rend plus difficile : le lancement demande des options supplémentaires (`-v`, `--env-file`), d'où l'intérêt de `compose.yaml` qui les écrit une fois pour toutes ; l'image seule ne suffit pas pour prédire.
- À surveiller : la présence du dossier `models/` et du `.env` sur la machine cible (`/health` doit répondre `model_loaded:true`) ; la cohérence entre la version de scikit-learn de l'image et celle de l'entraînement ; le compromis serait à revoir pour un déploiement où l'on veut un artefact unique et immuable (image construite en CI avec le modèle validé, par exemple).
