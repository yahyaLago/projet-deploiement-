# Compte rendu TP5 — Ahmed RAOUI

## Tests
```text
================== 32 passed, 4 warnings in 76.24s (0:01:16) ==================
```
Le starter comporte cinq tests de suivi qui nécessitent l'implémentation de log_run.
L'installation editable fait pointer maintai vers ce dossier TP5 plutôt que le TP4.

## MLflow
| Run | Recall | Precision | Accuracy | Identifiant | MD5 |
|---|---:|---:|---:|---|---|
| v1 défaut | 0.750 | 0.622 | 0.904 | `5b1af8f629bc426ab3c63fab94ffb6f8` | `73e0b7cb` |
| v1 C=0.01 | 0.691 | 0.653 | 0.908 | `4953b734031044088e56fdf45263d008` | `73e0b7cb` |
| v1 seuil 0.2 | 0.838 | 0.543 | 0.882 | `6cb8f1cadba24cd2a2d4cbc161c36fec` | `73e0b7cb` |
| v1 forêt | 0.728 | 0.562 | 0.886 | `8fd1e37186334a8db1961a3f3a8e0abd` | `73e0b7cb` |
| v2 défaut | 0.741 | 0.650 | 0.916 | `1de049dd139c4c39be1f57aa0b01e281` | `93fdeef2` |

Choix sur v1 : v1 seuil 0.2, recall 0.838, précision 0.543.
Une panne manquée est plus coûteuse qu'une fausse alerte. La forêt est comparée sur les mêmes données.
Version scikit-learn utilisée : 1.8.0. Le modèle MLflow conserve ses dépendances pour éviter les incompatibilités.
Les fichiers mlflow.db et mlruns ne doivent pas aller dans Git.

## DVC
Reçu v1 :
```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv

```
Le MD5 du reçu est identique au paramètre data_md5 des quatre runs v1.
Le CSV reste hors Git, le reçu léger est versionné.
État DVC lors de la modification :
```text
Non conservé par le premier script ; les deux reçus Git et leurs MD5 distincts ont été vérifiés lors de la reprise.
```
| Version | Commit | MD5 | Lignes |
|---|---|---|---:|
| v1 | `191613a6c5e42ca3156b7d4ceea449b60623a717` | `73e0b7cb` | 5000 |
| v2 | `0557a915700b8750d306f0cfef2b1ef369825a28` | `93fdeef2` | 8000 |

Retour v1 puis v2 vérifié par nombre de lignes et MD5.
Après suppression du CSV et du cache, dvc pull a restauré la v2 :
```text
A       data\sensors.csv
1 file fetched and 1 file added

```

## Comparaison v1/v2 à réglages identiques
| Version | MD5 | n_train | Recall | Precision |
|---|---|---:|---:|---:|
| v1 | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 | 93fdeef2 | 6400 | 0.741 | 0.650 |

Les jeux de test diffèrent : on ne peut pas conclure à une amélioration intrinsèque sans évaluation sur un jeu commun indépendant.

## Compréhension
Git versionne le code et les reçus, DVC les données, MLflow les entraînements et modèles.
Le remote local évite de publier un chemin personnel ; un stockage partagé serait nécessaire au groupe.
Le code, les données et le modèle sont retrouvables via Git, DVC et MLflow.
Le MD5 relie le run à un reçu DVC dans l'historique Git.

## Rendu
Pull request et tag tp5 : à vérifier après le push et la fusion du groupe.
