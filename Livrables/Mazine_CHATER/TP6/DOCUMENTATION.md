# Documentation — TP6

## Pourquoi Docker ?

Sur la machine du développeur, tout fonctionne « parce que les bonnes
bibliothèques sont installées ». Sur une autre machine, une version de
scikit-learn différente peut empêcher le chargement du modèle.

Une image Docker fige l'environnement : même système de base, mêmes
bibliothèques, même commande de démarrage. Le seul élément variable est ce
qu'on monte au lancement.

## Trois principes appliqués

### 1. Le cache des couches

Le `Dockerfile` copie d'abord `requirements-docker.txt`, installe les
bibliothèques, puis copie le code :

```dockerfile
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
COPY maintai maintai
COPY ui ui
```

Une modification du code ne réinstalle donc pas toutes les bibliothèques.
L'étape lente reste en cache tant que les dépendances ne changent pas.

### 2. Écouter sur `0.0.0.0`

```dockerfile
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`127.0.0.1` n'écouterait qu'à l'intérieur du conteneur : le port publié sur
le PC ne joindrait rien. `0.0.0.0` accepte les connexions venant de
l'extérieur du conteneur.

### 3. Séparer l'image des données

L'image ne contient ni `data/`, ni `models/`, ni `.env` :

- les données et le modèle sont montés en volume ;
- le secret arrive par `--env-file` ou `env_file:` dans Compose.

On peut donc reconstruire l'image, changer de modèle ou changer de clé sans
mélanger le code et les données.

## Compose : deux services

```yaml
services:
  api:
    build: .
    volumes:
      - ./models:/app/models:ro
  ui:
    image: maintai:0.4.0
    environment:
      MAINTAI_API_URL: http://api:8000
```

Dans un réseau Compose, les services se joignent par leur nom : l'interface
utilise `http://api:8000`, pas `localhost`. Sur le PC, l'utilisateur passe
par les ports publiés `8000` et `8501`.

## Choix techniques

**Une image unique pour l'API et l'interface.** Les deux utilisent le même
code et les mêmes bibliothèques. Deux images dupliqueraient les dépendances
sans bénéfice.

**`requirements-docker.txt` séparé.** L'image n'a besoin ni de MLflow, ni de
DVC, ni de pytest : elle sert le modèle, elle ne l'entraîne pas. Cela réduit
la taille et la surface d'attaque.

**Versions figées.** `scikit-learn==1.8.0` est la version qui a écrit le
modèle. Une version différente peut refuser de le charger.

**`.dockerignore` strict.** `.git`, `.venv`, `tests`, `data`, `models`,
`.env` et `mlflow.db` n'ont rien à faire dans l'image.

## Limites

- L'image n'est pas publiée dans un registre.
- L'API tourne sans HTTPS : à placer derrière un reverse proxy en réel.
- Le modèle est monté en lecture seule mais reste géré à la main.
