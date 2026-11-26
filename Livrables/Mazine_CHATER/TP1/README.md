# MaintAI — TP1

MaintAI estime la probabilité de panne d'une machine à partir de quatre
mesures : température, vibrations, charge et heures de fonctionnement.
Ce premier TP entraîne un modèle de classification et l'expose derrière
une API HTTP : un client envoie un relevé en JSON, le serveur renvoie une
probabilité et une alerte.

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

## Données et modèle

```bash
python -m maintai.dataset   # crée data/sensors.csv
python -m maintai.train     # crée models/model.joblib et les fichiers JSON
pytest                      # lance les tests
```

Le jeu de données est synthétique. Pour utiliser de vraies mesures, il suffit
de fournir un CSV avec les mêmes colonnes.

## Lancer l'API

```bash
uvicorn maintai.api.main:app --reload
```

- Documentation interactive : <http://localhost:8000/docs>
- État du service : `GET /health`
- Prédiction : `POST /v1/predict`

Exemple :

```bash
curl -X POST http://localhost:8000/v1/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"temperature_c\":72,\"vibration_mm_s\":6,\"load_pct\":85,\"runtime_hours\":15000}"
```

Une valeur hors plage, un champ manquant ou un champ inconnu est refusé
avec le code 422 : l'API ne devine jamais à la place du client.

## Organisation

```
maintai/
  config.py          chemins, seuil et contrat d'entrée
  dataset.py         génération des données synthétiques
  data.py            lecture du CSV et découpage entraînement / test
  train.py           entraînement, évaluation, sauvegarde
  predict.py         chargement du modèle et prédiction
  api/               routes FastAPI et schémas Pydantic
tests/               tests de l'API, des données et de l'entraînement
docs/adr/            décisions d'architecture
```

Les choix techniques sont expliqués dans `DOCUMENTATION.md`.
