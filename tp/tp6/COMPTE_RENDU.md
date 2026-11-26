# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G1  ·  **Membres :** Yahya Baid  ·  **Date :** 26/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!

Client:
 Version:           29.6.2

Server: Docker Desktop 4.83.0 (234302)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
================= 38 passed, 4 warnings in 157.92s (0:02:37) ==================
```

Le pytest a été lancé une fois les fichiers du sprint 2 écrits. Les 38 tests passent, y compris les 6 de `tests/test_docker.py`.

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   Une image est le résultat figé de la recette (`docker build -t maintai:0.4.0 .`) : les couches du Dockerfile, nommées et réutilisables. Un conteneur est une copie de cette image qui tourne, avec son propre système de fichiers et son propre réseau (`docker run ... maintai:0.4.0`).
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche. Docker réutilise toutes les couches jusqu'à la première qui change. Installer les bibliothèques est lent et change rarement ; le code change souvent. En copiant les requirements avant le code, un changement dans `maintai/` ne refait pas `pip install`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle a été enregistré avec scikit-learn 1.8.0. Une version plus récente ou plus ancienne peut refuser de charger `model.joblib`. La version est donc figée, la même que dans `requirements.txt`.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert l'API et l'interface. On n'entraîne pas, on ne versionne pas les données et on ne lance pas les tests dans le conteneur. Ces outils alourdiraient l'image sans servir au démarrage.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai maintai
COPY ui ui

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 8 min 43 s | 1.13GB (contenu 259MB) |
| après une modification de `maintai/predict.py` | 11 s | 1.13GB |

Que signifie `CACHED` dans le journal du second build ?

Docker a reconnu que les couches inchangées (image de départ, `WORKDIR`, copie de `requirements-docker.txt`, `pip install`) étaient identiques au build précédent et les a réutilisées. Seules `COPY maintai` et les couches suivantes ont été refaites, parce que `predict.py` avait changé.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` — HTTP 200 |
| `POST /v1/predict` sans clé | `{"detail":"Clé API absente ou invalide"}` — HTTP 401 |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"2026-11-26T09:46:03Z"}` — HTTP 200 |

Relevé envoyé : température 72 °C, vibration 6 mm/s, charge 85 %, 15 000 h. La clé est celle de `.env` (fichier non versionné).

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond 200 avec `{"status":"ok","model_loaded":false}`. `POST /v1/predict` avec la clé répond 503 : `Modèle non chargé`. L'image ne contient pas `models/`. Sans le volume, le processus démarre, mais `Predictor.load` ne trouve pas `model.joblib`.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` indique `Uvicorn running on http://127.0.0.1:8000`. `http://localhost:8002/health` échoue : `curl: (52) Empty reply from server`. Dans le conteneur, `127.0.0.1` désigne le conteneur lui-même, pas le PC. Le port publié `8002:8000` arrive sur l'interface réseau du conteneur, pas sur sa boucle locale, donc personne n'accepte la connexion. Il faut `--host 0.0.0.0`.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command:
      ["python", "-m", "streamlit", "run", "ui/app.py",
       "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       3 seconds ago   Up 2 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        3 seconds ago   Up 1 second    0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable `MAINTAI_API_URL`, posée sur le service `ui` dans `compose.yaml`. `ui/app.py` la lit avec `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`. `api` est le nom du service sur le réseau Compose, pas une adresse du PC.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
{"status":"ok","model_loaded":true}

httpx.ConnectError: [Errno 111] Connection refused
```

La première joint le service `api` par son nom DNS sur le réseau Compose. La seconde appelle `localhost` à l'intérieur du conteneur `ui` : c'est le conteneur de l'interface, qui n'écoute pas sur le port 8000. Le `localhost:8000` du navigateur, lui, est le PC, où le port 8000 est publié.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
================= 38 passed, 4 warnings in 157.92s (0:02:37) ==================
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

L'image `maintai:0.4.0` ne contient que le code et les bibliothèques figées, dont `scikit-learn==1.8.0`. Le modèle, les relevés et la clé API arrivent au lancement, par les volumes `./models` et `./data` en lecture seule et par `env_file: .env`, pour pouvoir les changer sans reconstruire l'image et sans laisser un secret dans un calque.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image : Python 3.11, les bibliothèques de `requirements-docker.txt` (`RUN pip install`), le code `maintai/` et `ui/` (`COPY`). Au lancement : le modèle par le volume `./models:/app/models:ro`, les données par `./data:/app/data:ro`, la clé API par `--env-file .env` ou `env_file: .env`, l'URL de l'API vue par l'interface par `MAINTAI_API_URL`.
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage et se reconstruit ; chaque `COPY` ou `ENV` d'un secret resterait dans l'historique des couches (`docker history`), même après un fichier effacé. `.env` est dans `.dockerignore`, et la clé n'est fournie qu'au `docker run` ou au `compose up`.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Le wheel (TP4) livre le code, MLflow et DVC (TP5) suivent l'entraînement et la version des données. Docker ajoute l'environnement d'exécution : le système, la version de Python et les bibliothèques exactes, de sorte que le même modèle tourne sur un PC ou un serveur sans y préparer de `.venv`.

## 8. Le rendu Git

- Lien de la pull request : branche `tp6-yahya-baid` sur https://github.com/yahyaLago/projet-deploiement-
- Le tag `tp6` existe sur GitHub : oui, posé sur le commit fusionné dans `main`
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? non — ils sont listés dans `.gitignore` (`.env`, `models/`, `data/*.csv`)

## 9. Ce qui reste flou

La différence entre le `localhost` du PC et le `localhost` d'un conteneur. Le navigateur joint l'API publiée sur le PC ; depuis le conteneur `ui`, il faut le nom `api`.
