# MaintAI — TP5

Le TP5 rend les entraînements comparables et les données reproductibles :

- **MLflow** enregistre chaque entraînement (paramètres, métriques, modèle,
  empreinte des données).
- **DVC** versionne le fichier de données sans le mettre dans Git.

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Entraîner et comparer

```bash
python -m maintai.dataset
python -m maintai.train                        # régression logistique, C=1.0
python -m maintai.train --C 0.01               # autre régularisation
python -m maintai.train --threshold 0.2        # autre seuil d'alerte
python -m maintai.train --model forest         # forêt aléatoire
mlflow ui                                      # http://localhost:5000
```

Chaque run contient :

| Élément | Exemple |
|---|---|
| paramètres | `model`, `C`, `threshold`, `n_train`, `data_md5` |
| métriques | `accuracy`, `recall`, `precision`, `baseline_recall` |
| modèle | le pipeline complet, avec ses dépendances |

## Versionner les données avec DVC

```bash
dvc add data/sensors.csv            # crée data/sensors.csv.dvc
git add data/sensors.csv.dvc .gitignore
git commit -m "Version 1 des données"

dvc remote add --local -d stockage C:/dvc-stockage
dvc push
```

Pour changer de version :

```bash
python -m maintai.dataset --n 8000 --seed 7
dvc add data/sensors.csv
git commit -am "Version 2 des données"
```

Pour revenir en arrière :

```bash
git checkout HEAD~1 -- data/sensors.csv.dvc
dvc checkout
```

Le fichier `.dvc` contient l'empreinte MD5 et la taille. Le CSV lui-même
n'est pas versionné par Git : il est stocké par DVC.

## Tests

```bash
pytest
```

Les tests de suivi vérifient qu'un run est créé, que les métriques et
l'empreinte des données sont enregistrées, et que le modèle peut être
rechargé depuis MLflow.

## Organisation

```
maintai/
  tracking.py        enregistrement d'un run MLflow
  train.py           entraînement + appel à log_run
  ...
data/sensors.csv.dvc version DVC du jeu de données
docs/adr/            décisions d'architecture
```

Les choix techniques sont expliqués dans `DOCUMENTATION.md`.
