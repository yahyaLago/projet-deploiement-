# TP6 — Conteneuriser MaintAI

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 26/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp6`

---

## 1. Mise en place

Le TP6 se fait dans `tp/tp6`, avec Docker Desktop et l'environnement Python du projet.

```powershell
docker run hello-world
docker version
python -m pytest
```

La première ligne de `docker run hello-world` confirme que le démon répond :

```text
Hello from Docker!
```

Pour `docker version`, je relève les deux lignes demandées :

```text
Client:
 Version:           29.6.2

Server: Docker Desktop 4.83.0 (234302)
```

Après la mise en place, `pytest` donne :

```text
================= 38 passed, 4 warnings in 157.92s (0:02:37) ==================
```

Au départ, les tests de `tests/test_docker.py` qui lisent `Dockerfile`, `requirements-docker.txt`, `.dockerignore` et `compose.yaml` échouent, car ces fichiers n'existent pas encore. Le test de l'interface, lui, peut déjà passer. Une fois les fichiers écrits, les 38 tests passent.

Ces tests ne lancent pas Docker. Ils vérifient les fichiers et le comportement de l'interface avec `AppTest`, ce qui permet de les exécuter sans démon Docker. Le vrai contrôle de l'image reste le `docker build` et le `docker run` décrits plus bas.

## 2. Image et conteneur

**1. Quelle différence entre une image et un conteneur ?**  
Une image est le résultat figé d'une recette : les couches du `Dockerfile`, nommées et réutilisables. Un conteneur est une instance de cette image en cours d'exécution, avec sa couche d'écriture, ses processus et son réseau. L'image `maintai:0.4.0` peut servir à lancer plusieurs conteneurs, chacun isolé.

**2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?**  
Chaque instruction crée une couche. Docker réutilise les couches tant que l'instruction et son contenu n'ont pas changé. `pip install` est lent et ne change que lorsque les dépendances changent ; le code change souvent. En copiant les requirements avant le code, une modification dans `maintai/` ne refait pas l'installation.

**3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?**  
Le modèle a été enregistré avec scikit-learn 1.8.0. Une version plus récente peut afficher un avertissement de compatibilité, voire refuser de charger `model.joblib`. L'image doit reproduire l'environnement qui a produit le modèle, pas un environnement quelconque. La version est donc figée, comme dans `requirements.txt`.

**4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?**  
L'image sert l'API et l'interface. On n'entraîne pas, on ne versionne pas les données et on ne lance pas les tests dans le conteneur. Ces outils alourdissent l'image, augmentent la surface d'attaque et n'ont aucun rôle au démarrage.

## 3. Sprint 1 : le Dockerfile

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

| Build | Durée | Taille de l'image |
|---|---|---|
| premier build | 8 min 43 s | 1.13 Go (contenu 259 Mo) |
| après une modification de `maintai/predict.py` | 11 s | 1.13 Go |

**Que signifie `CACHED` dans le second build ?** Docker reconnaît que l'image de départ, le `WORKDIR`, la copie de `requirements-docker.txt` et le `pip install` sont identiques au build précédent. Il réutilise ces couches. Seules `COPY maintai` et les couches suivantes sont refaites, car `predict.py` a changé. C'est exactement l'effet recherché par l'ordre des instructions.

Le second build reste très rapide parce que le code est petit et que l'installation des bibliothèques est la partie lente. Si j'avais copié le code avant les requirements, chaque modification aurait relancé `pip install`.

## 4. Sprint 1 : lancer un conteneur

```powershell
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

Sous PowerShell, j'utilise `${PWD}` là où un terminal `cmd` utiliserait `%cd%`. Le volume doit recevoir un chemin absolu du PC ; un chemin relatif serait interprété différemment par le démon.

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` — HTTP 200 |
| `POST /v1/predict` sans clé | `{"detail":"Clé API absente ou invalide"}` — HTTP 401 |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"2026-11-26T09:46:03Z"}` — HTTP 200 |

Le relevé envoyé est température 72 °C, vibration 6 mm/s, charge 85 %, 15 000 heures. La clé est celle de `.env`, un fichier non versionné.

**Piège 1 — sans le volume `models`.**  
`/health` répond 200 avec `{"status":"ok","model_loaded":false}`. `POST /v1/predict` avec la clé répond 503 : `Modèle non chargé`. L'image ne contient pas `models/`. Sans le volume, le processus démarre quand même, mais `Predictor.load` ne trouve pas `model.joblib`. C'est volontaire : l'API reste diagnostiquable, et le modèle peut être changé sans reconstruire l'image.

**Piège 2 — avec `--host 127.0.0.1`.**  
`docker logs test` indique `Uvicorn running on http://127.0.0.1:8000`. Pourtant, `http://localhost:8002/health` échoue :

```text
curl: (52) Empty reply from server
```

Dans le conteneur, `127.0.0.1` désigne le conteneur lui-même, pas le PC. Le port publié `8002:8000` arrive sur l'interface réseau du conteneur, mais le processus n'écoute que sur sa boucle locale. Personne n'accepte la connexion. Il faut `--host 0.0.0.0` pour écouter sur toutes les interfaces du conteneur.

## 5. Sprint 2 : Docker Compose

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

`docker compose ps` :

```text
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       3 seconds ago   Up 2 seconds   0.0.0.0:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        3 seconds ago   Up 1 second    0.0.0.0:8501->8501/tcp
```

**Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?**  
Elle affiche `http://api:8000`. Cette valeur vient de `MAINTAI_API_URL`, posée sur le service `ui` dans `compose.yaml`. `ui/app.py` la lit avec `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`. `api` est le nom du service sur le réseau Compose, pas une adresse du PC.

**Les deux commandes `docker compose exec ui ...`.**  
La première interroge le service par son nom :

```text
{"status":"ok","model_loaded":true}
```

La seconde interroge `localhost` depuis le conteneur `ui` :

```text
httpx.ConnectError: [Errno 111] Connection refused
```

La première passe par le DNS interne de Compose. La seconde appelle le conteneur `ui` lui-même, qui n'écoute pas sur le port 8000. Le `localhost:8000` du navigateur, lui, est le PC, où le port 8000 est publié.

À la fin du sprint 2 :

```text
================= 38 passed, 4 warnings in 157.92s (0:02:37) ==================
```

Les 38 tests couvrent l'API (7), le client (3), les données (3), la sécurité (5), l'entraînement (3), le packaging (2), le suivi MLflow (5), l'interface (2), la CLI (2) et Docker (6).

## 6. Décision : l'ADR 005

L'ADR `docs/adr/005-image-docker.md` retient une image qui ne contient que le code et les bibliothèques figées, dont `scikit-learn==1.8.0`. Le modèle, les données et la clé API arrivent au lancement, par les volumes `./models` et `./data` en lecture seule et par `env_file: .env`. L'API écoute sur `0.0.0.0:8000` pour être joignable à travers le port publié.

Conséquences : un changement de code ou de dépendance impose un rebuild ; un nouvel entraînement se limite à remplacer le dossier `models/` monté ; la clé n'apparaît jamais dans `docker history`. Sans le volume `models`, `/health` indique `model_loaded: false` et la prédiction répond 503.

## 7. Questions de compréhension

**1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ?**

| Élément | Où | Moyen |
|---|---|---|
| Python 3.11 et le système de base | Image | `FROM python:3.11-slim` |
| Bibliothèques (`numpy`, `pandas`, `scikit-learn`, `fastapi`, `uvicorn`, `streamlit`) | Image | `RUN pip install -r requirements-docker.txt` |
| Code `maintai/` et `ui/` | Image | `COPY maintai maintai`, `COPY ui ui` |
| Modèle (`model.joblib`, `model_info.json`) | Lancement | volume `./models:/app/models:ro` |
| Données (`sensors.csv`) | Lancement | volume `./data:/app/data:ro` |
| Clé API | Lancement | `--env-file .env` ou `env_file: .env` |
| URL de l'API vue par l'interface | Lancement | variable `MAINTAI_API_URL` |

**2. Pourquoi la clé API n'est-elle jamais dans l'image ?**  
Une image se partage et se reconstruit. Chaque `COPY` ou `ENV` d'un secret reste dans l'historique des couches (`docker history`), même si le fichier est supprimé ensuite. `.env` est dans `.dockerignore`, et la clé n'est fournie qu'au `docker run` ou au `compose up`. On peut ainsi changer la clé sans reconstruire l'image.

**3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?**  
Le wheel du TP4 livre le code, MLflow et DVC suivent l'entraînement et la version des données. Docker ajoute l'environnement d'exécution complet : le système, la version de Python et les bibliothèques exactes. Le même modèle démarre sur un PC ou un serveur sans préparer de `.venv`, à condition de fournir le modèle, les données et la clé.

## 8. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier :** `tp/tp6`
- **Mon fichier :** `CR_TP6_Mazine_CHATER.md`
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp6`
- **Fichiers exclus :** `.venv`, `.env`, `models/`, `data/*.csv`, `mlflow.db`, `mlruns/`
- **Fichiers versionnés :** `Dockerfile`, `compose.yaml`, `.dockerignore`, `requirements-docker.txt`, le code et les ADR

## 9. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| `python:3.11-slim` | C'est la même version mineure que l'environnement de développement, avec une image de base plus légère que la version complète. Le code n'a pas besoin des outils de compilation pour fonctionner : les wheels de numpy, pandas et scikit-learn sont disponibles. |
| Pas d'image Alpine | Alpine utilise musl à la place de glibc. Les wheels binaires de numpy, pandas et scikit-learn peuvent manquer ou être recompilés, ce qui allonge le build et crée des écarts de comportement. `slim` reste compatible avec l'environnement de développement. |
| `WORKDIR /app` | Tous les chemins de l'image sont stables. Les volumes, les variables `MAINTAI_MODELS_DIR` et `MAINTAI_DATA_PATH` et la commande `uvicorn` peuvent utiliser `/app` sans dépendre du répertoire courant. |
| `requirements-docker.txt` séparé | L'image n'a besoin que des bibliothèques d'exécution. Ce fichier exclut `mlflow`, `dvc`, `pytest`, `build` et les outils de développement. L'image est plus petite et ne contient pas d'outils inutiles au service. |
| Versions figées avec `==` | Le modèle a été sérialisé avec `scikit-learn==1.8.0`. Une version différente peut produire un avertissement ou un résultat faux. Les versions figées rendent le build reproductible. |
| Requirements copiés avant le code | Le `pip install` est la couche lente. En la gardant avant `COPY maintai`, une modification du code ne la refait pas. C'est le rôle du cache de couches. |
| `pip install --no-cache-dir` | Le cache de pip ne sert plus après l'installation. Le supprimer évite de stocker des archives inutiles dans la couche et réduit la taille de l'image. |
| Copier seulement `maintai/` et `ui/` | L'image n'a pas besoin des tests, des données, du modèle, de la documentation ni de l'historique Git. Copier le strict nécessaire réduit la taille et la surface d'attaque. |
| `.dockerignore` | Il protège même si un `COPY . .` est ajouté plus tard : `.env`, `models/`, `data/`, `.git/`, `mlflow.db`, `mlruns/`, `.dvc/`, `tests/` et les caches n'entrent jamais dans le contexte. |
| `ENV MAINTAI_MODELS_DIR` et `MAINTAI_DATA_PATH` | Le code lit déjà ces variables dans `config.py`. Les fixer dans l'image donne des chemins cohérents avec les volumes, sans modifier le code pour le conteneur. |
| `EXPOSE 8000` | Déclare le port utilisé par l'API. Ce n'est pas ce qui publie le port, mais cela documente l'image et aide les outils qui l'inspectent. La publication réelle se fait avec `-p 8000:8000`. |
| `--host 0.0.0.0` | Le processus doit écouter sur l'interface réseau du conteneur pour être joignable depuis le port publié. `127.0.0.1` ne écoute que la boucle locale du conteneur, ce qui rend le service injoignable depuis le PC. |
| Ni modèle ni données dans l'image | Le modèle change à chaque entraînement et les données changent de version. Les inclure imposerait un rebuild à chaque fois et alourdirait l'image. Les volumes permettent de les remplacer à chaud. |
| Volumes montés en `:ro` | Le conteneur n'a besoin que de lire le modèle et les données. Le mode lecture seule évite qu'un bug ou une commande modifie les fichiers du PC. |
| `.env` fourni au lancement | La clé API est un secret. Elle ne doit pas être dans une couche. `env_file: .env` ou `--env-file .env` la injecte au démarrage, et `.dockerignore` empêche son entrée dans le contexte de build. |
| La même image pour l'API et l'interface | Les deux services partagent le même code et les mêmes bibliothèques. Réutiliser `maintai:0.4.0` évite un second build et garantit qu'ils tournent dans le même environnement. Seule la commande change. |
| Commande Streamlit surchargée | L'image démarre l'API par défaut. Le service `ui` remplace la commande par `python -m streamlit run ...` avec `--server.address=0.0.0.0` et `--server.headless=true`. C'est plus simple qu'une seconde image. |
| `MAINTAI_API_URL: http://api:8000` | Sur le réseau Compose, `api` est le nom DNS du service. `localhost` désignerait le conteneur `ui`. L'URL est ainsi valable sur n'importe quelle machine, sans dépendre du port publié sur le PC. |
| `depends_on: api` | Compose démarre l'API avant l'interface. Cela ne garantit pas que l'API est prête à répondre : `depends_on` ne fait pas de healthcheck. L'interface gère l'erreur si l'API n'est pas encore disponible. Pour un vrai déploiement, il faudrait un `healthcheck` et une condition `service_healthy`. |
| Pas de champ `version:` dans `compose.yaml` | Compose v2 n'en a plus besoin et l'ancien champ produit un avertissement. Le fichier reste plus court et conforme au format actuel. |
| Pas de `restart` ni de `healthcheck` | C'est un choix de TP local : on veut voir les erreurs et arrêter les conteneurs facilement. En production, j'ajouterais `restart: unless-stopped` et un healthcheck sur `/health`. |
| Pas de build multi-étapes | L'image finale n'a besoin ni de compilateur ni d'outils de build : les wheels sont installés directement. Un multi-stage ajouterait de la complexité sans gain mesurable ici. Il deviendrait utile si une étape compilait des dépendances. |
| Ports `8000` et `8501` | Ils correspondent aux ports de développement et au README. L'utilisateur retrouve les mêmes URL qu'en local, et le navigateur n'a pas besoin d'un port différent. |
| Tag `maintai:0.4.0` | Il correspond à `__version__` du package. Le numéro rend l'image identifiable et permet de garder plusieurs versions lors des essais. |
| Tests Docker statiques | `pytest` ne lance pas Docker : il vérifie les fichiers qui cassent un conteneur sans bruit (ordre des couches, `0.0.0.0`, secrets exclus, volume du modèle). C'est rapide et utilisable sans démon, mais cela ne remplace pas un `docker build` et un `docker run` réels. |

## 10. Ce que je retiens

Docker ne remplace ni le wheel, ni MLflow, ni DVC. Il ajoute l'environnement d'exécution : le système, Python et les bibliothèques exactes. Le modèle, les données et la clé restent à l'extérieur de l'image, ce qui permet de les changer sans reconstruire.

Les deux pièges du TP m'ont le plus appris. Sans volume, l'API démarre mais ne peut pas prédire : le modèle n'est pas dans l'image. Avec `--host 127.0.0.1`, le conteneur écoute uniquement sur lui-même et le port publié ne sert à rien. Ce sont des erreurs silencieuses : le conteneur tourne, mais le service est injoignable ou incomplet.

Ce qui reste ouvert : la configuration de production. Il faudrait un healthcheck, une politique de redémarrage, un registre d'images et une procédure de mise à jour. Je n'ai pas non plus cherché à réduire la taille de l'image au-delà de `slim` et `--no-cache-dir` ; un build multi-étapes ou une image plus spécialisée serait la prochaine étape.
