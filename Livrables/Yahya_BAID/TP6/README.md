# MaintAI

Application de prédiction de panne à partir de relevés de capteurs, construite pas à pas pendant le cours « Développement et déploiement d'applications intelligentes ».

Les données fournies sont synthétiques : `python -m maintai.dataset` les génère. Elles se remplacent par des données réelles qui gardent les mêmes colonnes.

## Installation

```bash
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# Linux / macOS :
source .venv/bin/activate

pip install -r requirements.txt
```

## Données et entraînement

```bash
python -m maintai.dataset      # écrit data/sensors.csv
python -m maintai.train        # écrit models/model.joblib, model_info.json, metrics.json
pytest                          # lance tous les tests
```

## Lancer l'API

```bash
uvicorn maintai.api.main:app --reload
```

Documentation interactive : http://localhost:8000/docs

## Clé API et client web

```bash
cp .env.example .env            # puis changez MAINTAI_API_KEY
uvicorn maintai.api.main:app --reload --env-file .env
python -m http.server 5500 -d web   # dans un second terminal
```

Ouvrez http://localhost:5500 et saisissez la clé définie dans `.env`.

## Interface Streamlit (TP3)

```bash
uvicorn maintai.api.main:app --reload --env-file .env   # terminal 1
python -m streamlit run ui/app.py                        # terminal 2
```

Ouvrez http://localhost:8501, saisissez l'URL de l'API et la clé dans la barre latérale.
Onglet « Données » : le jeu de données ; onglet « Prédiction » : un relevé envoyé à l'API.

## Installer MaintAI comme un package (TP4)

```bash
pip install -r requirements.txt   # versions figées, celles du modèle
pip install -e .                  # installe maintai en mode éditable
maintai-predict 72 6 85 15000     # la commande déclarée dans pyproject.toml
streamlit run ui/app.py           # fonctionne maintenant sans python -m
```

Construire la distribution : `python -m build` écrit `dist/maintai-0.2.0-py3-none-any.whl`.
Le wheel contient le code, pas le modèle : sur une autre machine, indiquez son dossier dans `MAINTAI_MODELS_DIR`.

## Suivre les entraînements avec MLflow (TP5)

```bash
python -m maintai.train                        # un run : régression logistique, C=1.0
python -m maintai.train --C 0.01               # un autre réglage
python -m maintai.train --threshold 0.2        # un autre seuil d'alerte
python -m maintai.train --model forest         # un autre modèle
mlflow ui                                      # http://localhost:5000, mode « Model training »
```

Chaque run enregistre ses paramètres, l'empreinte des données (`data_md5`), ses métriques et le modèle,
avec les versions exactes des bibliothèques. Les runs sont dans `mlflow.db` et `mlruns/` (non versionnés).

## Versionner les données avec DVC (TP5)

```bash
dvc init --subdir                              # dans TP/TP5
dvc add data/sensors.csv                       # crée data/sensors.csv.dvc (versionné par Git)
dvc remote add --local -d stockage C:/dvc-stockage
dvc push                                       # copie les données dans le stockage
python -m maintai.dataset --n 8000 --seed 7    # une nouvelle version des données
dvc add data/sensors.csv && git commit ...     # nouvelle version
git checkout HEAD~1 -- data/sensors.csv.dvc && dvc checkout   # revenir à la version précédente
dvc pull                                       # récupérer les données depuis le stockage
```

## Lancer MaintAI avec Docker (TP6)

```bash
python -m maintai.dataset & python -m maintai.train   # le modèle, dans models/
copy .env.example .env                                  # puis choisir une clé
docker build -t maintai:0.4.0 .                         # l'image : code + bibliothèques
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
docker rm -f maintai-api
docker compose up -d --build                            # l'API (8000) et l'interface (8501)
docker compose down
```

L'image ne contient ni le modèle, ni les données, ni la clé : ils arrivent au lancement (volumes, `--env-file`).

## Structure

```
maintai/            code du projet
  config.py         chemins et paramètres
  dataset.py        génération des données synthétiques
  data.py           chargement et découpage
  train.py          entraînement, évaluation, sauvegarde
  predict.py        chargement du modèle et prédiction
  api/              API FastAPI (TP1, TP2)
  client.py         client HTTP de l'API (TP3)
  cli.py            commande maintai-predict (TP4)
  tracking.py       suivi des entraînements avec MLflow (TP5)
web/                client web HTML/JS (TP2)
ui/                 interface Streamlit (TP3)
tests/              tests pytest
docs/adr/           décisions d'architecture
pyproject.toml      fiche d'identité du package (TP4)
data/sensors.csv.dvc  version des données suivie par DVC (TP5)
Dockerfile          recette de l'image (TP6)
compose.yaml        l'API et l'interface en deux conteneurs (TP6)
requirements-docker.txt  bibliothèques de l'image, versions figées (TP6)
```
