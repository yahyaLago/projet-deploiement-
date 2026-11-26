# ADR 002 — Validation du modèle

## Contexte

Une accuracy élevée peut cacher un modèle qui ne détecte aucune panne,
puisque les pannes sont minoritaires. Il faut une évaluation qui reflète le
risque réel.

## Décision

1. Découper les données en 80 % pour l'entraînement et 20 % pour le test.
2. Stratifier ce découpage sur la colonne `failure`.
3. Comparer le modèle à une baseline qui prédit toujours la classe
   majoritaire.
4. Mesurer l'accuracy, le rappel et la précision **au seuil d'alerte**, pas
   au seuil 0,5 par défaut.

## Pourquoi

- La stratification garantit que le jeu de test contient la même proportion
  de pannes que le jeu d'entraînement.
- La baseline rend le gain du modèle vérifiable : sans elle, une accuracy de
  0,89 ne dit pas si le modèle apprend quelque chose.
- Le rappel est la métrique prioritaire : une panne non détectée a un coût
  plus élevé qu'une fausse alerte.
- Évaluer au seuil réel évite l'incohérence classique entre les métriques
  annoncées et le comportement en production.

## Conséquences

Le seuil est enregistré avec le modèle. Le jeu de test ne sert jamais à
régler le seuil : ce réglage devra se faire sur un jeu de validation séparé
lors d'une prochaine itération.

## Limite

Un seul découpage ne donne pas d'intervalle de confiance. Pour aller plus
loin, il faudrait une validation croisée.
