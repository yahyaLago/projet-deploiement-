# ADR 005 — Image Docker

## Contexte

L'application dépend de versions précises de Python et de bibliothèques.
Une installation manuelle sur une autre machine est lente et fragile,
surtout lorsque le modèle doit être rechargé avec la même version de
scikit-learn.

## Décision

Construire une image Docker unique qui sert l'API et l'interface, avec :

- `python:3.11-slim` comme base ;
- des versions figées dans `requirements-docker.txt` ;
- les bibliothèques installées avant le code ;
- un lancement sur `0.0.0.0:8000` ;
- les données, le modèle et la clé fournis au lancement, jamais dans
  l'image.

## Pourquoi

- L'environnement devient reproductible : la même image se comporte de la
  même façon partout.
- L'ordre des couches garde le cache de `pip` : reconstruire après une
  modification de code prend quelques secondes.
- Séparer l'image des données évite de reconstruire l'image à chaque
  réentraînement et empêche un secret de finir dans une couche.
- Une seule image limite la duplication : l'API et l'interface partagent le
  code et les dépendances.

## Conséquences

- Il faut entraîner le modèle sur la machine avant de démarrer le conteneur.
- Le modèle est monté dans `/app/models` en lecture seule.
- La clé API est lue depuis `.env`, ignoré par Git et par `.dockerignore`.
- Les tests Docker vérifient les fichiers, pas le démarrage réel : la CI
  devra lancer `docker build` pour compléter.

## Alternatives écartées

- **Installer directement sur la machine** : pas reproductible.
- **Deux images séparées** : duplication inutile des dépendances.
- **Mettre le modèle dans l'image** : image lourde et obsolète dès le
  prochain entraînement.
- **`127.0.0.1` dans la commande** : inaccessible depuis le PC.
