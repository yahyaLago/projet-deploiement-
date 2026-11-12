# MaintAI

Application de prédiction de panne à partir de relevés de capteurs, construite pas à pas pendant le cours **Développement et déploiement d'applications intelligentes**.

**Auteur :** Yahya Baid  
**Livrable :** TP3 — interface Streamlit

Les données fournies sont synthétiques : `python -m maintai.dataset` les génère. Elles se remplacent par des données réelles qui gardent les mêmes colonnes.

Le compte rendu détaillé du TP3 se trouve dans [`COMPTE_RENDU.md`](COMPTE_RENDU.md). Les décisions d’architecture sont dans [`docs/adr/000-modele.md`](docs/adr/000-modele.md) et [`docs/adr/004-interface-streamlit.md`](docs/adr/004-interface-streamlit.md) (séance 6 · une interface).

## Installation

Toutes les commandes ci-dessous s'exécutent depuis la racine du projet (`maintai-starter-tp3`).

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
python -m pytest               # lance tous les tests
```

## Lancer l'API

```bash
# Windows (PowerShell)
$env:MAINTAI_API_KEY="test-key"
python -m uvicorn maintai.api.main:app --reload --host 127.0.0.1 --port 8001
```

```bash
# Linux / macOS
MAINTAI_API_KEY=test-key python -m uvicorn maintai.api.main:app --reload --host 127.0.0.1 --port 8001
```

Documentation interactive : http://127.0.0.1:8001/docs

## Clé API et client web (TP2)

```bash
copy .env.example .env          # Windows — puis changez MAINTAI_API_KEY
# cp .env.example .env          # Linux / macOS
python -m uvicorn maintai.api.main:app --reload --env-file .env --host 127.0.0.1 --port 8001
python -m http.server 5500 -d web   # dans un second terminal
```

Ouvrez http://localhost:5500 et saisissez la clé définie dans `.env`.

## Interface Streamlit (TP3)

Deux terminaux, depuis la racine du projet :

```bash
# Terminal 1 — API
python -m uvicorn maintai.api.main:app --reload --env-file .env --host 127.0.0.1 --port 8001

# Terminal 2 — interface
python -m streamlit run ui/app.py
```

Ouvrez http://localhost:8501, saisissez l'URL de l'API (`http://127.0.0.1:8001`) et la clé dans la barre latérale.

| Onglet | Rôle |
|---|---|
| Données | Indicateurs du jeu, taux de panne par tranche, nuage température / vibration |
| Prédiction | Envoi d'un relevé à l'API via `MaintaiClient` |

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
web/                client web HTML/JS (TP2)
ui/                 interface Streamlit (TP3)
tests/              tests pytest
docs/adr/           décisions d'architecture (dont 004 · interface Streamlit)
COMPTE_RENDU.md     compte rendu du TP3
```

## Auteur

Yahya Baid — TP3 MaintAI.
