# MaintAI — TP2

Le TP2 protège l'API du TP1 et ajoute un client web. Un relevé envoyé en
JSON donne toujours une probabilité de panne et une alerte, mais il faut
maintenant présenter la bonne clé API.

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
```

## Clé API et origines autorisées

Copiez `.env.example` en `.env`, puis choisissez une clé :

```dotenv
MAINTAI_API_KEY=une-cle-longue-et-imprevisible
MAINTAI_CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

Le fichier `.env` n'est jamais versionné.

## Lancer l'API et le client web

```bash
uvicorn maintai.api.main:app --reload --env-file .env
python -m http.server 5500 -d web
```

- API : <http://localhost:8000/docs>
- Client web : <http://localhost:5500>

Sans clé, ou avec une mauvaise clé, `/v1/predict` répond 401.
`/health` reste public pour permettre la supervision.

## Tests

```bash
pytest
```

Les tests couvrent l'absence de clé, une clé fausse, les origines CORS
autorisées et refusées, ainsi que les rejets de validation.

## Organisation

```
maintai/
  config.py          chemins, seuil, clé API et origines CORS
  dataset.py         génération des données
  data.py            lecture et découpage
  train.py           entraînement et sauvegarde
  predict.py         prédiction
  api/
    main.py          routes et chargement du modèle
    schemas.py       validation des entrées et sorties
    security.py      vérification de la clé API
web/index.html       client HTML/JavaScript
tests/               tests unitaires et d'intégration
docs/adr/            décisions d'architecture
```

Les choix techniques sont détaillés dans `DOCUMENTATION.md`.
