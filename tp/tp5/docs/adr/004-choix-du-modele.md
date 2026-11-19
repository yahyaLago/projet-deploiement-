# ADR 004 : Choix du modèle et du seuil MaintAI

Date : 19/11/2026 · Auteurs : Yahya Baid

## Contexte

MaintAI doit détecter les pannes à partir des relevés des capteurs. Une panne manquée est considérée plus coûteuse qu'une fausse alerte; le rappel (recall) est donc le critère prioritaire, tout en surveillant la précision.

Les runs comparés utilisent les mêmes réglages (régression logistique, `C=1.0`, seuil `0.2`) sur deux versions de données. La v1 contient 5 000 relevés (`data_md5=b7fec4274774842dc1f48202c6013490`); la v2 en contient 8 000 (`data_md5=31ef5ebb63ef2331a31dfe009ef8796a`).

## Options étudiées

Les quatre essais initiaux sur v1 :

| Modèle / paramètres | Rappel | Précision | Exactitude |
|---|---:|---:|---:|
| Régression logistique, `C=1.0`, seuil `0.2` | 0.838 | 0.543 | 0.882 |
| Régression logistique, `C=1.0`, seuil `0.3` | 0.750 | 0.622 | 0.904 |
| Régression logistique, `C=0.01`, seuil `0.3` | 0.691 | 0.653 | 0.908 |
| Forêt aléatoire, seuil `0.3` | 0.728 | 0.562 | 0.886 |

Comparaison du même réglage (`logreg`, `C=1.0`, seuil `0.2`) entre versions :

| Version / run | Données (MD5) | n_train | Rappel | Précision | Exactitude |
|---|---|---:|---:|---:|---:|
| v1 / `hilarious-bear-847` | `b7fec4274774842dc1f48202c6013490` | 4 000 | 0.838 | 0.543 | 0.882 |
| v2 / `fun-dove-613` | `31ef5ebb63ef2331a31dfe009ef8796a` | 6 400 | 0.824 | 0.567 | 0.897 |

## Décision

Retenir provisoirement la régression logistique avec `C=1.0` et un seuil de décision de `0.2`. Elle offre le meilleur rappel observé des essais comparés (0.838 sur v1 contre 0.824 sur v2), conformément à la priorité de réduire les pannes manquées. La différence est faible; le run v2 présente une meilleure précision et exactitude.

Run de référence : `hilarious-bear-847` (`run_id=c83e9ea5946b4d258932046d6b7348e6`), entraîné sur v1.

Run comparatif v2 : `fun-dove-613` (`run_id=6f2ba3ea99e24c2bb9c6e18ba15d6a4a`), `data_md5=31ef5ebb63ef2331a31dfe009ef8796a`.

## Conséquences

Le réglage retenu a la meilleure détection des pannes mesurée, mais la précision de la v1 (`0.543`) implique davantage de fausses alertes que sur la v2 (`0.567`). Les versions ont des volumes et compositions de données différents et leurs découpages train/test ne sont pas identiques; la comparaison ne prouve donc pas à elle seule une supériorité générale. Valider le choix sur des données de test représentatives et suivre le compromis entre pannes manquées et fausses alertes avant le déploiement.
