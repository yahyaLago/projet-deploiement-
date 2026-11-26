# ADR 004 : choix du modèle MaintAI

Auteur : Ahmed RAOUI

## Contexte
Une panne manquée est plus coûteuse qu'une fausse alerte.

## Options
Régression logistique par défaut, C=0.01, seuil 0.2 et forêt aléatoire, comparées sur v1.

## Décision
v1 seuil 0.2 ; modèle `logreg`, seuil `0.2`.
Recall : 0.838 ; précision : 0.543.
Run : `6cb8f1cadba24cd2a2d4cbc161c36fec`.
data_md5 : `73e0b7cb3c6f795c70c3ddf970b99c15`.

## Conséquences
Priorité au recall, quitte à accepter davantage de fausses alertes.
Surveiller la précision et la dérive ; réévaluer sur un jeu indépendant commun.
