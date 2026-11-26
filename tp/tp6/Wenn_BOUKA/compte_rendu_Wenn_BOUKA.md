# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Étudiant :** Wenn BOUKA  ·  **Groupe :** Yahya BAID, Ahmed RAOUI, Wenn BOUKA, Mazine CHATER  ·  **Date :** 26/11/2026  ·  **Dossier :** `tp/tp6/Wenn_BOUKA`

> **Conditions d'exécution, en toute transparence.**
> - Le code (Dockerfile, `.dockerignore`, `compose.yaml`, `ui/app.py`), les tests `pytest` et les essais de l'API lancée avec Uvicorn hors conteneur ont été réalisés par un assistant IA (Claude), dans un environnement Linux cloud (Python 3.11.18), le 26/11/2026.
> - Les étapes Docker et Docker Compose ont été exécutées sur Windows avec le script `run_tp6.ps1`, qui a rempli automatiquement les valeurs mesurées ci-dessous (Microsoft Windows NT 10.0.19045.0, PowerShell 5.1.19041.6456, Python 3.13.3). Docker Hub n'était pas joignable depuis l'environnement cloud : aucune valeur Docker de ce document n'y a été mesurée.
> - Les deux dossiers du groupe (`Ahmed_RAOUI`, `Wenn_BOUKA`) ont été préparés de la même manière, avec l'assistance de l'IA. Les résultats sont identiques à ceux du dossier `Ahmed_RAOUI` parce que le code et les graines aléatoires sont les mêmes ; aucune différence n'a été inventée.

---

## 1. Mise en place (dans `tp/tp6/Wenn_BOUKA`)

Sortie de `docker run hello-world` (première ligne utile) et de `docker version` :

```
Hello from Docker!
Client: 29.9.3  Server: 29.9.3
Docker Compose version v5.7.0
```

`python -m maintai.dataset` : 5000 relevés écrits (taux de panne : 13.6 %). `python -m maintai.train` : modèle sauvegardé dans `models/` (accuracy 0.904, rappel 0.75, précision 0.622, seuil 0.3 ; baseline : accuracy 0.864, rappel 0).

Dernière ligne de `python -m pytest` après la mise en place (environnement cloud, avant les sprints) :

```
5 failed, 33 passed, 4 warnings in 11.45s
```

Les cinq échecs étaient tous dans `tests/test_docker.py`, comme annoncé par le polycopié.

## 2. Image et conteneur

1. **Quelle différence entre une image et un conteneur ?**
   Le **Dockerfile** est la recette (un fichier texte, une instruction par ligne). L'**image** est le résultat figé et nommé de cette recette (`maintai:0.4.0`) : un système de fichiers en lecture seule, composé de couches, avec Python, les bibliothèques et le code. Le **conteneur** est une copie de l'image qui tourne, isolée : il a son propre processus, son réseau et une couche de fichiers inscriptible qui disparaît quand on le supprime. Une image peut lancer plusieurs conteneurs (ici `api` et `ui` partent de la même image).
2. **Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?**
   Chaque instruction crée une **couche**, et au build suivant Docker réutilise toutes les couches jusqu'à la première qui change. L'installation des bibliothèques est lente et change rarement ; le code est rapide à copier et change souvent. En copiant d'abord le seul fichier de dépendances puis en lançant `pip install`, une modification du code n'invalide que les couches `COPY maintai` et suivantes : `pip install` reste en cache.
3. **Pourquoi `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?**
   Le modèle `model.joblib` a été écrit par scikit-learn 1.8.0 (TP4). Un pickle n'est garanti relisible que par la même version ; avec `>=1.5`, un build ultérieur pourrait installer une autre version et charger le modèle avec des avertissements, des erreurs ou des prédictions différentes. Figer toutes les versions rend aussi le build reproductible (le test `test_image_requirements_are_pinned_like_the_model` le vérifie).
4. **Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?**
   L'image sert le modèle : elle n'entraîne pas, ne versionne pas les données et ne lance pas de tests. Ces outils alourdiraient l'image, rallongeraient le build et augmenteraient la surface d'attaque sans rien apporter à l'exécution.

## 3. Sprint 1 : le Dockerfile

```dockerfile
# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# 1. L'image de départ : la même version de Python que sur nos PC, en version slim
FROM python:3.11-slim

# 2. Le dossier de travail dans l'image
WORKDIR /app

# 3. Les bibliothèques AVANT le code : cette étape lente reste en cache tant que
#    requirements-docker.txt ne change pas
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Le code (change souvent : couches rapides, reconstruites à chaque modification)
COPY maintai ./maintai
COPY ui ./ui

# 5. Où le code trouve le modèle et les données : ils arrivent par des volumes au lancement
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Le port de l'API, et la commande de démarrage, à l'écoute de toutes les adresses
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée (mesurée par `Measure-Command`) | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 21.3 s | maintai:0.4.0  1.13GB |
| après une modification de `maintai/predict.py` | 3.9 s | (même ordre de grandeur, seules les couches du code changent) |

Lignes `CACHED` du second build :

```
#6 CACHED
#7 CACHED
#8 CACHED
```

**Que signifie `CACHED` ?** Docker a reconnu que l'instruction et ses entrées (fichiers copiés, couche précédente) n'avaient pas changé : il réutilise la couche déjà construite au lieu de réexécuter l'étape. Au second build, `FROM`, `WORKDIR`, `COPY requirements-docker.txt` et surtout `RUN pip install` sont en cache ; seules `COPY maintai` (le fichier modifié) et les instructions suivantes sont reconstruites, d'où l'écart de durée entre les deux builds. La ligne ajoutée dans `predict.py` pour l'expérience a ensuite été retirée et l'image reconstruite avec le code d'origine.

`.dockerignore` exclut, en plus des lignes du starter : `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/`, `.dvc/`, ainsi que `docs/`, `web/`, `*.md` et `releve.json`, inutiles à l'exécution.

## 4. Sprint 1 : lancer un conteneur

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "C:\Users\Cloud\Downloads\tp6_livrables\tp\tp6\Wenn_BOUKA\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse dans le conteneur (Windows) | Réponse hors conteneur (Uvicorn, environnement cloud) |
|---|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true} [HTTP 200]` | `{"status":"ok","model_loaded":true}` [200] |
| `POST /v1/predict` sans clé | `{"detail":"Cl├⌐ API absente ou invalide"} [HTTP 401]` | `{"detail":"Clé API absente ou invalide"}` [401] |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"2026-11-26T11:03:36Z"} [HTTP 200]` | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,...}` [200] |
| `GET /docs` (Swagger) | HTTP 200 | HTTP 200 |

Relevé utilisé : `{"temperature_c": 72, "vibration_mm_s": 6, "load_pct": 85, "runtime_hours": 15000}`.

Fin de `docker logs maintai-api` :

```
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.17.0.1:57078 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:57094 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:57106 - "POST /v1/predict HTTP/1.1" 401 Unauthorized
INFO:     172.17.0.1:57110 - "POST /v1/predict HTTP/1.1" 200 OK
INFO:     172.17.0.1:57120 - "GET /docs HTTP/1.1" 200 OK
```

**Piège 1 : sans l'option `-v ...models...`.**

- `/health` : `{"status":"ok","model_loaded":false} [HTTP 200]`
- `/v1/predict` avec la clé : `{"detail":"Mod├¿le non charg├⌐ : lancez python -m maintai.train puis red├⌐marrez l'API"} [HTTP 503]`

L'API démarre, mais `/app/models` n'existe pas dans le conteneur : le modèle n'est pas dans l'image (exclu par `.dockerignore`) et aucun volume ne l'apporte. `/health` répond donc `model_loaded:false` et `/v1/predict` renvoie 503 « Modèle non chargé ». Le même comportement a été observé hors conteneur en pointant `MAINTAI_MODELS_DIR` vers un dossier vide : `model_loaded:false` puis 503. C'est voulu : l'image porte le code, le modèle arrive au lancement.

**Piège 2 : `--host 127.0.0.1`.**

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

`http://localhost:8002/health` : `[HTTP 000]`

Les journaux montrent qu'Uvicorn tourne normalement, mais sur `127.0.0.1`, c'est-à-dire l'interface de bouclage **du conteneur**. Le port publié `-p 8002:8000` fait arriver les requêtes du PC sur l'interface réseau du conteneur (son adresse sur le réseau Docker), pas sur son `127.0.0.1` : personne n'y écoute, la connexion est fermée et le navigateur n'obtient aucune réponse. Avec `0.0.0.0`, Uvicorn écoute sur toutes les interfaces du conteneur, y compris celle où arrive le trafic publié.

## 5. Sprint 2 : Docker Compose

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    volumes:
      - ./models:/app/models:ro        # le modèle vient du PC, en lecture seule

  ui:
    image: maintai:0.4.0               # la même image, une autre commande
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000 # l'API vue depuis ce conteneur : le nom du service
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro            # les relevés pour l'onglet « Données »
    depends_on:
      - api
```

Dans `ui/app.py`, la valeur par défaut de la barre latérale est maintenant lue dans l'environnement :

```python
url = st.text_input("URL de l'API", os.getenv("MAINTAI_API_URL", "http://localhost:8000"))
```

Sortie de `docker compose ps` :

```
NAME               IMAGE           COMMAND                  SERVICE   CREATED          STATUS          PORTS
wenn_bouka-api-1   maintai:0.4.0   "uvicorn maintai.apiΓÇª"   api       18 seconds ago   Up 16 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
wenn_bouka-ui-1    maintai:0.4.0   "python -m streamlitΓÇª"   ui        17 seconds ago   Up 16 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Fin de `docker compose logs api` :

```
api-1  | INFO:     Started server process [1]
api-1  | INFO:     Waiting for application startup.
api-1  | INFO:     Application startup complete.
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
api-1  | INFO:     172.19.0.1:40956 - "GET /health HTTP/1.1" 200 OK
```

API publiée : `{"status":"ok","model_loaded":true} [HTTP 200]` · Interface (`/_stcore/health` sur le port 8501) : `ok [HTTP 200]`

**Quelle URL affiche la barre latérale ? D'où vient-elle ?** `MAINTAI_API_URL` dans le conteneur `ui` vaut `http://api:8000`. Elle vient de la clé `environment` du service `ui` dans `compose.yaml`, lue par `os.getenv` dans `ui/app.py`. Lancée hors Compose, sans cette variable, l'interface garde `http://localhost:8000`.

Prédiction faite depuis le conteneur `ui`, avec le même client (`MaintaiClient`) que l'interface et l'URL `http://api:8000` :

```
{'failure_probability': 0.9475, 'alert': True, 'threshold': 0.3, 'model_version': '2026-11-26T11:03:36Z'}
```

Hors conteneur (environnement cloud), Streamlit lancé avec `MAINTAI_API_URL=http://localhost:8000` répondait `ok` sur `/_stcore/health`, et le même client renvoyait une probabilité de 0.9475 (alerte, seuil 0.3). La prédiction par clic dans le navigateur et sa capture sont faites manuellement sur le PC (pause prévue dans `run_tp6.ps1`) ; les tests `test_ui.py` et `test_docker.py` couvrent l'affichage de la prédiction et la lecture de la variable.

**Les deux commandes `docker compose exec ui ...` :**

```
api       -> {"status":"ok","model_loaded":true}
localhost -> httpx.ConnectError: [Errno 111] Connection refused
```

La seconde échoue parce que, dans un conteneur, `localhost` désigne **ce conteneur lui-même**. Dans le conteneur `ui`, seul Streamlit tourne, rien n'écoute sur le port 8000 : connexion refusée. Le navigateur, lui, tourne sur le PC, où `localhost:8000` est le port publié par le service `api`. Compose crée un réseau commun où chaque service est joignable par son nom : depuis `ui`, l'API est `http://api:8000` (résolution DNS interne de Docker).

**`docker compose down` : que supprime-t-elle ?**

```
Container wenn_bouka-ui-1 Stopping 
 Container wenn_bouka-ui-1 Stopped 
 Container wenn_bouka-ui-1 Removing 
 Container wenn_bouka-ui-1 Removed 
 Container wenn_bouka-api-1 Stopping 
 Container wenn_bouka-api-1 Stopped 
 Container wenn_bouka-api-1 Removing 
 Container wenn_bouka-api-1 Removed 
 Network wenn_bouka_default Removing 
 Network wenn_bouka_default Removed
```

Elle arrête et **supprime les conteneurs** des services et le **réseau** créé par Compose. Elle ne supprime ni l'image `maintai:0.4.0` (il faudrait `--rmi`), ni les volumes nommés (il faudrait `-v`), ni surtout les dossiers du PC montés (`models/`, `data/`) : le modèle et les données survivent, et `docker compose up` les retrouve.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
Environnement cloud (Linux) : 38 passed, 4 warnings in 11.52s
Windows (run_tp6.ps1)       : 38 passed, 4 warnings in 76.71s (0:01:16)
```

Aucune assertion des tests du professeur n'a été modifiée.

## 6. Décision : l'ADR 005

Voir `docs/adr/005-image-docker.md`. Le modèle n'entre pas dans l'image : il arrive par un volume en lecture seule, ce qui permet de changer de modèle sans reconstruire l'image et garde celle-ci légère et partageable. Données, secrets et fichiers d'entraînement restent hors de l'image grâce à `.dockerignore` ; la clé arrive au lancement par `env_file: .env`.

## 7. Questions de compréhension

1. **Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ?**
   Dans l'image : Python 3.11 (`FROM`), les bibliothèques figées (`RUN pip install`), le code `maintai/` et `ui/` (`COPY`), les chemins par défaut (`ENV`) et la commande (`CMD`). Au lancement : le modèle (volume `./models:/app/models:ro`), les données (volume `./data:/app/data:ro` pour l'interface), la clé API (`--env-file .env` ou `env_file`), l'URL de l'API pour l'interface (`environment`), et les ports (`-p` ou `ports`).
2. **Pourquoi la clé API n'est-elle jamais dans l'image ?**
   Une image se partage (registre, collègues, serveur) et chaque couche peut être inspectée (`docker history`, extraction des fichiers) : un secret qui y entre est publié. Il faudrait aussi reconstruire l'image pour changer la clé. Passée au lancement, elle reste sur la machine qui exécute et se change sans rebuild.
3. **Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?**
   Après le paquet (TP4), le suivi MLflow et le versionnement DVC (TP5), Docker livre **l'environnement d'exécution complet** : système, version de Python et bibliothèques figées, avec la commande de démarrage. L'API tourne de la même façon sur tout PC ou serveur équipé de Docker, sans `.venv` à préparer, et Compose décrit dans un fichier le lancement de l'API et de l'interface ensemble.

## 8. Le rendu Git

- Branche : `tp6-wenn-bouka` (partie de `origin/main`, ne contient que `tp/tp6/Wenn_BOUKA`).
- Lien de la pull request : PR_A_VENIR
- Le tag `tp6` existe sur GitHub : non. Il sera posé collectivement après relecture et fusion des pull requests.
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? Non. Ils sont ignorés par `.gitignore`, et le script de push refuse de commiter s'il en trouve, ou s'il trouve la clé API dans un fichier. L'image ne va pas dans Git : elle se reconstruit à partir du Dockerfile.

## 9. Ticket de sortie

1. **Quelle différence entre une image et un conteneur ?** L'image est le modèle figé et nommé (code + bibliothèques, en couches, en lecture seule) ; le conteneur est une instance de cette image qui tourne, isolée, avec sa propre couche inscriptible.
2. **Pourquoi le modèle n'est-il pas dans l'image ?** Il change sans nouveau code : il arrive par un volume, ce qui évite un rebuild à chaque réentraînement et garde l'image légère. Une seule image peut servir plusieurs versions du modèle.
3. **Pourquoi `ui` appelle-t-il `http://api:8000` et pas `localhost` ?** Dans le conteneur `ui`, `localhost` est le conteneur `ui` lui-même ; l'API est un autre conteneur, joignable sur le réseau Compose par le nom de son service, `api`.
4. **Qu'est-ce qui reste flou ?** Comment publier l'image sur un registre (Docker Hub, GitHub Container Registry) et la déployer sur un serveur ; ce qu'il faut ajouter en production (utilisateur non root, `HEALTHCHECK`, redémarrage automatique).
