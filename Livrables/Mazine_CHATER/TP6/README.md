# MaintAI — TP6

Le TP6 emballe l'API et l'interface dans des conteneurs Docker. L'image
contient le code et les bibliothèques ; elle ne contient ni les données, ni
le modèle, ni la clé API. Ces trois éléments sont fournis au lancement.

## Préparer le modèle sur la machine

```bash
python -m maintai.dataset
python -m maintai.train
copy .env.example .env        # puis choisir MAINTAI_API_KEY
```

## Construire et lancer

```bash
docker build -t maintai:0.4.0 .

docker run -d --name maintai-api ^
  -p 8000:8000 ^
  --env-file .env ^
  -v "%cd%\models:/app/models:ro" ^
  maintai:0.4.0
```

- API : <http://localhost:8000/docs>
- Arrêt : `docker rm -f maintai-api`

Avec Docker Compose, l'API et l'interface démarrent ensemble :

```bash
docker compose up -d --build
docker compose down
```

- API : <http://localhost:8000>
- Interface : <http://localhost:8501>

## Ce que contient l'image

| Élément | Dans l'image ? | Pourquoi |
|---|---|---|
| code `maintai/` et `ui/` | oui | c'est l'application |
| bibliothèques de `requirements-docker.txt` | oui | versions figées |
| `data/` | non | volume, peut changer sans reconstruire |
| `models/` | non | volume, entraîné sur la machine |
| `.env` | non | secret |
| `mlflow.db`, `tests/` | non | inutiles au service |

## Tests

```bash
pytest
```

Les tests Docker ne lancent pas Docker : ils vérifient les fichiers qui
cassent un conteneur sans message clair (ordre des couches, adresse
d'écoute, secrets exclus, volumes Compose).

## Organisation

```
Dockerfile               recette de l'image
compose.yaml             API + interface
.dockerignore            ce qui n'entre pas dans l'image
requirements-docker.txt  bibliothèques du conteneur, versions figées
maintai/                 code
ui/                      interface Streamlit
tests/                   tests
```

Les choix techniques sont expliqués dans `DOCUMENTATION.md`.
