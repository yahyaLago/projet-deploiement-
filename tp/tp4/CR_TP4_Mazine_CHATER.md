# TP4 — MaintAI devient un package Python

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 12/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp4`

---

## 1. Mise en place

Le TP4 se fait dans `tp/tp4`, avec son propre environnement virtuel.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
```

Juste après l'installation, j'obtiens :

```text
FAILED tests/test_package.py::test_installed_version_matches_the_code
FAILED tests/test_package.py::test_command_is_declared
2 failed, 25 passed, 1 warning
```

Les deux échecs viennent du fait que `maintai` n'est pas encore installé comme package :

- `test_installed_version_matches_the_code` appelle `importlib.metadata.version("maintai")`. Cette fonction lit les métadonnées d'un package installé par pip. Pour l'instant, `maintai` n'est qu'un dossier importable depuis le répertoire courant, donc aucune métadonnée n'existe.
- `test_command_is_declared` cherche la commande `maintai-predict` parmi les points d'entrée de l'environnement. La section `[project.scripts]` n'est pas encore écrite et le package n'est pas installé, donc la commande n'existe pas.

Le code fonctionne, mais pip ne le connaît pas encore.

## 2. Sprint 1 : `pyproject.toml` et installation éditable

Les sections ajoutées dans `pyproject.toml` :

```toml
dependencies = [
    "pandas>=2.2",
    "numpy>=1.26",
    "scikit-learn>=1.4",
    "joblib>=1.3",
    "httpx>=0.27",
    "pydantic>=2.0",
    "python-dotenv>=1.0"
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

**Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?**  
`dependencies` décrit ce dont le code de `maintai/` a besoin pour fonctionner chez n'importe quel utilisateur : pandas, scikit-learn, joblib, etc. Tout le monde n'a pas besoin de l'API ni de l'interface. `fastapi` et `uvicorn` sont donc dans le groupe optionnel `api`, Streamlit dans `ui`, et les outils de développement dans `dev`. On les installe avec `pip install maintai[api]`, `maintai[ui]` ou `maintai[dev]`. Cela garde l'installation de base légère et limite les conflits de versions.

```powershell
pip install -e .
maintai-predict --version
pip show maintai
```

Les premières lignes de `pip show maintai` :

```text
Name: maintai
Version: 0.2.0
Summary: Package Python de maintenance prédictive permettant d'estimer le risque de panne des machines à partir de données de capteurs
Home-page:
```

À la fin du sprint 1 :

```text
27 passed, 1 warning
```

### Depuis un autre dossier

Je me place dans `%TEMP%` et je lance les deux commandes demandées :

```text
> maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)

> python -c "import maintai; print(maintai.__file__)"
C:\...\tp\tp4\maintai\__init__.py
```

La commande fonctionne depuis n'importe quel dossier, et `maintai.__file__` pointe vers mon dossier de travail, pas vers `site-packages`. C'est le principe de `pip install -e .` : pip ne copie pas le code, il crée un lien dans l'environnement vers le dossier du projet. Python trouve donc toujours les fichiers sources.

Le modèle est trouvé de la même manière : `config.py` calcule `ROOT` à partir de `__file__`, donc le dossier `models/` reste celui du projet.

**Modification du message dans `cli.py`.** J'ai remplacé « Probabilité de panne : » par « Risque de panne estimé : ». En relançant `maintai-predict` sans réinstaller, le nouveau message apparaît immédiatement. C'est normal en mode éditable : le `.exe` appelle `maintai.cli:main`, et ce module est lu directement dans les sources. Il faut réinstaller seulement si l'on modifie `pyproject.toml`, car les métadonnées et le point d'entrée sont créés à l'installation. J'ai remis le message d'origine ensuite.

## 3. Sprint 2 : construire et installer le wheel

```powershell
python -m build
dir dist
```

```text
maintai-0.2.0-py3-none-any.whl
maintai-0.2.0.tar.gz
```

Contenu du wheel :

```text
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/...
```

Le modèle, les tests et `ui/` ne sont pas dans le wheel. La configuration `[tool.setuptools.packages.find] include = ["maintai*"]` ne fait entrer que le package `maintai/` et son sous-dossier `api/`.

C'est un choix volontaire : le wheel livre le code. Les tests servent au développement, l'interface Streamlit est une application à part, et le modèle est un fichier lourd, régénérable par l'entraînement. Le modèle est donc distribué séparément, et son dossier est indiqué par `MAINTAI_MODELS_DIR`.

### Essai dans un environnement neuf

Dans `%TEMP%\essai`, j'installe le wheel puis je lance la commande :

| Étape | Ce qui s'affiche |
|---|---|
| Sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : ...\essai\.venv\Lib\site-packages\models\model.joblib`, puis le conseil d'entraîner le modèle ou d'indiquer son dossier. |
| Avec `MAINTAI_MODELS_DIR` vers mes `models` | `InconsistentVersionWarning` (modèle écrit avec scikit-learn 1.8.0, version 1.9.1 utilisée), puis `Probabilité de panne : 95 % (ALERTE)`. |
| Après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement. |

L'avertissement vient de la version de scikit-learn. Le wheel déclare `scikit-learn>=1.4` ; dans l'environnement neuf, pip a donc installé la dernière version disponible. Or `model.joblib` est un objet sérialisé avec la version 1.8.0. Au chargement, scikit-learn détecte l'écart et prévient que le résultat peut être faux.

La ligne de `models/model_info.json` qui explique cela est :

```json
"sklearn_version": "1.8.0"
```

En installant exactement cette version, l'avertissement disparaît.

## 4. Réponses aux questions

**1. Différence entre `requirements.txt` et `dependencies` ?**  
`dependencies` donne des versions minimales (`>=`) : c'est le contrat du package, assez souple pour s'installer avec d'autres bibliothèques. `requirements.txt` fige des versions exactes (`==`) : il reproduit l'environnement dans lequel le modèle a été entraîné. Il contient aussi les outils de développement et d'interface, qui ne font pas partie du package.

**2. Différence entre `pip install -e .` et l'installation du wheel ?**  
`pip install -e .` installe en mode éditable : pip crée un lien vers les sources, donc chaque modification est visible sans réinstallation. C'est l'installation de développement. Le wheel est une archive figée : pip copie les fichiers dans `site-packages`, et le projet source n'est plus nécessaire. Une modification du code exige de reconstruire et de réinstaller le wheel.

**3. Qu'est-ce qu'un point d'entrée ? Où pip crée-t-il `maintai-predict.exe` ?**  
Un point d'entrée associe un nom de commande à une fonction Python, au format `commande = "module:fonction"`. Ici, `maintai-predict = "maintai.cli:main"`. À l'installation, pip génère un petit exécutable qui importe `maintai.cli` et appelle `main()`. Sous Windows, il se trouve dans le dossier `Scripts` de l'environnement actif, par exemple `tp\tp4\.venv\Scripts\maintai-predict.exe`. Ce dossier est dans le `PATH` quand l'environnement est activé.

## 5. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier :** `tp/tp4`
- **Mon fichier :** `CR_TP4_Mazine_CHATER.md`
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp4`
- **`git status` avant le commit :** `dist/`, `build/` et `maintai.egg-info/` n'apparaissent pas, car ils sont dans `.gitignore`
- **Fichiers exclus :** `.venv`, `models/`, `dist/`, `build/`, `*.egg-info/`

## 6. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| `pyproject.toml` avec le backend setuptools | C'est le format standard des packages Python modernes. Setuptools suffit pour ce projet et évite d'ajouter un outil de plus. |
| Version dynamique lue dans `maintai.__version__` | Une seule valeur fait foi. Les métadonnées du package ne peuvent donc pas diverger de la version réellement importée. |
| Dépendances en `>=` | Le package doit pouvoir cohabiter avec d'autres projets. Des versions minimales évitent de bloquer inutilement l'utilisateur tout en garantissant les fonctionnalités nécessaires. |
| Groupes optionnels `api`, `ui` et `dev` | Tout le monde n'a pas besoin de FastAPI, Streamlit ou pytest. Les rendre optionnels garde l'installation de base légère et réduit les conflits de versions. |
| `[project.scripts]` | Le point d'entrée déclare la commande `maintai-predict` et la fonction à appeler. Pip génère l'exécutable au moment de l'installation. |
| `pip install -e .` | En développement, on veut voir immédiatement ses modifications. Le mode éditable crée un lien vers les sources au lieu de copier le code. |
| Wheel pour la livraison | Il faut une archive figée et installable sans le dépôt ni les sources. L'utilisateur du wheel n'a pas besoin de Git. |
| `python -m build` plutôt qu'un script maison | L'outil standard construit le sdist et le wheel à partir de `pyproject.toml`. Il évite de réécrire la logique de packaging et produit des archives conformes. |
| Wheel limité à `maintai*` | Le package ne doit contenir que le code d'exécution. Les tests, l'interface et le modèle sont des artefacts ou des applications séparées. |
| Modèle absent du wheel | Le modèle est lourd, régénérable et lié à une version de scikit-learn et à un jeu de données. Le livrer séparément permet de le remplacer sans reconstruire le package. |
| `MAINTAI_MODELS_DIR` et `ROOT` calculé depuis `__file__` | Le code ne dépend pas du répertoire courant. En mode éditable, `ROOT` pointe vers le projet ; une fois installé, la variable d'environnement indique où trouver le modèle. |
| `requires-python = ">=3.11"` | Le code utilise les annotations modernes, comme le type optionnel `str` ou `None`, et les versions testées. Python 3.11 est le socle minimal réaliste. |
| `pytest` et `fastapi` hors de `dependencies` | Ce sont des outils de développement ou des extras. Les inclure dans le cœur alourdirait l'installation et imposerait des versions inutiles à un utilisateur de la commande. |
| `requirements.txt` avec des versions exactes | Il reproduit l'environnement d'entraînement, notamment la version de scikit-learn qui a sérialisé le modèle. C'est indispensable pour éviter les problèmes de compatibilité du fichier joblib. |
| Ne pas figer scikit-learn dans `pyproject.toml` | Un `==` dans le package entrerait en conflit avec les autres projets de l'utilisateur. Mieux vaut un fichier de contraintes ou une vérification de version au chargement du modèle. |
| `dist/`, `build/` et `*.egg-info/` ignorés | Ces dossiers sont générés par la construction. Les versionner créerait des différences inutiles et des binaires dans l'historique Git. |
| Environnement neuf pour tester le wheel | Il prouve que l'installation fonctionne sans dépendre du projet source ni des paquets déjà présents dans l'environnement de développement. |

## 7. Ce que je retiens

Le mode éditable est très pratique pendant le développement : on modifie un fichier et le changement est immédiatement pris en compte. Le wheel, lui, correspond au moment de la livraison : le code est figé et copié dans l'environnement de l'utilisateur.

Ce qui reste ouvert pour moi, c'est la livraison du modèle. Faut-il le publier dans un stockage séparé avec un numéro de version, l'inclure dans le wheel, ou vérifier sa version au chargement ? Je n'ai pas encore de réponse satisfaisante. Le deuxième point est la version de scikit-learn : `>=` dans `pyproject.toml` est souple, mais un modèle entraîné avec une version précise peut mal se charger avec une version plus récente. Un fichier de contraintes ou un contrôle de version au démarrage serait probablement plus sûr.
