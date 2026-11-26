# ADR 005 : ce que contient l'image Docker de MaintAI

Date : 26/11/2026 · Auteurs : Yahya Baid (G1)

## Contexte

MaintAI sert un modèle scikit-learn déjà entraîné. L'image doit démarrer de la même façon sur n'importe quelle machine, mais le modèle, les relevés et la clé API changent sans que le code change, et la clé ne doit pas se retrouver dans un calque d'image.

## Options étudiées

1. Tout copier dans l'image (code, bibliothèques, `models/`, `data/`, `.env`) : un seul `docker run` suffit, mais chaque nouvel entraînement ou chaque rotation de clé impose un rebuild, le secret reste dans l'historique des calques, et l'image grossit avec des fichiers qui ne servent pas à exécuter l'API.
2. N'image que le code et les bibliothèques figées (`requirements-docker.txt`, dont `scikit-learn==1.8.0`), et fournir le reste au lancement : volume `./models:/app/models:ro`, volume `./data:/app/data:ro`, clé via `env_file: .env`.

## Décision

On retient l'option 2. L'image `maintai:0.4.0` contient le code (`maintai/`, `ui/`) et les bibliothèques épinglées à la version qui a produit le modèle. Le modèle, les données et la clé API arrivent au lancement, par volumes en lecture seule et par variable d'environnement. L'API écoute sur `0.0.0.0:8000` pour être joignable à travers le port publié.

## Conséquences

Un changement de code ou de dépendance reconstruit l'image ; un nouvel entraînement se limite à remplacer le dossier `models/` monté, sans rebuild. La clé n'est jamais dans `docker history`. Il faut fournir le volume et le fichier `.env` à chaque lancement : sans `models/`, `/health` répond `model_loaded: false` et `/v1/predict` répond 503. `mlflow`, `dvc` et `pytest` restent hors de l'image : on n'entraîne pas et on ne teste pas dans le conteneur qui sert l'API.
