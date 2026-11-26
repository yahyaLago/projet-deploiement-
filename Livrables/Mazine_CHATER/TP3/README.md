# MaintAI — TP3

Le TP3 ajoute une interface Streamlit et un client Python réutilisable.
L'interface sert à deux choses : comprendre les données, puis envoyer un
relevé à l'API et lire la prédiction.

## Installation et démarrage

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
copy .env.example .env        # puis choisir MAINTAI_API_KEY
```

Trois terminaux :

```bash
# 1. l'API
uvicorn maintai.api.main:app --reload --env-file .env

# 2. l'interface
python -m streamlit run ui/app.py

# 3. les tests
pytest
```

Ouvrez <http://localhost:8501>, saisissez l'URL de l'API et la clé dans la
barre latérale.

## Les deux onglets

- **Données** : nombre de relevés, taux de panne, température moyenne,
  histogramme du taux de panne par tranche et nuage de points
  température / vibration.
- **Prédiction** : quatre curseurs, un bouton, puis la probabilité et
  l'alerte renvoyées par l'API.

## Le client Python

`maintai/client.py` isole les appels HTTP. L'interface ne connaît ni `httpx`
ni le format des erreurs : elle appelle `predict()` et reçoit un dictionnaire.

```python
from maintai.client import MaintaiClient

api = MaintaiClient("http://localhost:8000", api_key="ma-cle")
reponse = api.predict({
    "temperature_c": 72,
    "vibration_mm_s": 6,
    "load_pct": 85,
    "runtime_hours": 15000,
})
```

## Organisation

```
maintai/
  client.py          appels HTTP vers l'API
  ...
ui/app.py            interface Streamlit
releve.json          exemple de relevé
tests/               tests, dont ceux du client et de l'interface
docs/adr/            décisions d'architecture
```

Les choix techniques sont expliqués dans `DOCUMENTATION.md`.
