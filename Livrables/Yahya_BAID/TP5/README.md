# MaintAI — TP5

Ce TP ajoute le suivi des entraînements avec MLflow et le versionnement des
données avec DVC.

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
python -m maintai.train
python -m maintai.train --C 0.01
python -m maintai.train --threshold 0.2
python -m maintai.train --model forest
mlflow ui
```

Chaque run enregistre les paramètres (`model`, `C`, `threshold`, `n_train`,
`data_md5`), les métriques (`accuracy`, `recall`, `precision`,
`baseline_recall`) et le modèle complet.

## Versionner les données avec DVC

```bash
dvc add data/sensors.csv
git add data/sensors.csv.dvc
git commit -m "Version 1 des données"

dvc remote add --local -d stockage C:/dvc-stockage
dvc push
```

Le CSV n'est pas versionné par Git : seul le fichier `.dvc` l'est. Pour
récupérer les données sur une autre machine : `dvc pull`.

## Tests

```bash
pytest
```

## Organisation

```
maintai/tracking.py       enregistrement d'un run MLflow
maintai/train.py          entraînement et appel à log_run
data/sensors.csv.dvc      version DVC des données
docs/adr/                 décisions d'architecture
```
