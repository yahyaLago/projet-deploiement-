# ADR 000 — Choix du modèle

## Contexte

MaintAI doit estimer une probabilité de panne à partir de quatre mesures de
capteurs. Le jeu de données est petit, synthétique et déséquilibré : les
pannes sont minoritaires.

## Décision

Utiliser une régression logistique précédée d'une standardisation, dans un
seul `Pipeline` scikit-learn.

## Pourquoi

- Elle produit directement une probabilité, ce qui permet de choisir un seuil
  d'alerte adapté au coût d'une panne manquée.
- Elle est rapide à entraîner et à recharger, donc simple à déployer.
- Ses coefficients restent interprétables, ce qui aide à expliquer le modèle.
- Le `Pipeline` embarque la standardisation : impossible d'oublier le
  prétraitement au moment de la prédiction.

## Conséquences

Le seuil d'alerte est un paramètre à part entière. Il est enregistré dans
`model_info.json` avec la version du modèle, afin que l'évaluation et la
prédiction utilisent exactement le même.

## Alternatives écartées

- **Forêt aléatoire** : plus complexe, sans gain démontré sur ce volume de
  données ; elle sera proposée plus tard comme option de comparaison.
- **Règle manuelle sur les seuils de capteurs** : difficile à calibrer et à
  maintenir dès que les machines changent.
