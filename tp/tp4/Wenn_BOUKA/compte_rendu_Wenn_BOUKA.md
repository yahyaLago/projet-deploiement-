# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** G1  ·  **Membre :** Wenn BOUKA  ·  **Date :** 20/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp4/Wenn_BOUKA`

---

## 1. Mise en place (dans `tp/tp4/Wenn_BOUKA`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```text
FAILED tests/test_package.py::test_installed_version_matches_the_code - importlib.metadata.PackageNotFoundError: No package metadata was found for maintai
FAILED tests/test_package.py::test_command_is_declared - AssertionError: assert 'maintai-predict' in [...]
2 failed, 25 passed, 1 warning
```

**Quels sont les deux tests qui échouent, et pourquoi ?**

Les deux tests de `tests/test_package.py`, qui ne regardent pas le code mais **l'installation** :

- `test_installed_version_matches_the_code` appelle `importlib.metadata.version("maintai")`, qui lit les métadonnées d'un package installé par pip. `import maintai` fonctionne déjà, mais seulement parce que le dossier courant est dans `sys.path` : pip n'a jamais installé `maintai`, aucune métadonnée n'existe, d'où `PackageNotFoundError`.
- `test_command_is_declared` cherche `maintai-predict` parmi les points d'entrée `console_scripts` de l'environnement. Tant que `[project.scripts]` n'est pas écrit et le package pas installé, la commande n'existe pas.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Mes sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=1.26",
    "pandas>=2.2",
    "scikit-learn>=1.4",
    "joblib>=1.3",
    "httpx>=0.27",  # maintai/client.py
]

[project.optional-dependencies]
api = ["fastapi>=0.115", "uvicorn[standard]>=0.30"]  # fastapi apporte pydantic (schemas.py)
ui = ["streamlit>=1.40"]
dev = ["pytest>=8", "ruff"]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

J'ai construit la liste à partir des `import` réellement présents dans `maintai/` (hors `maintai/api/`) : numpy, pandas, scikit-learn, joblib, httpx. Je n'ai pas mis `python-dotenv`, qu'aucun module n'importe (c'est uvicorn qui lit `.env` avec `--env-file`), ni `pydantic`, utilisé seulement par `api/schemas.py` et déjà apporté par `fastapi` dans le groupe `api`.

**Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?**

`dependencies` est ce qu'il faut pour **utiliser** le package, chez n'importe qui. Le collègue qui lance `maintai-predict` n'a besoin ni de pytest (outil de développeur, groupe `dev`) ni de fastapi/uvicorn (seulement pour faire tourner l'API, groupe `api`, installé avec `pip install "maintai[api]"`). Les imposer alourdirait chaque installation et multiplierait les risques de conflit de versions. Je l'ai vérifié dans l'environnement neuf de la partie 3 : après installation du wheel, `import fastapi` échoue (`ModuleNotFoundError`) et `maintai-predict` fonctionne quand même.

Sortie de `pip show maintai` (les quatre premières lignes) :

```text
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne de machines à partir de relevés de capteurs (MaintAI)
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```text
27 passed, 1 warning
```

**Depuis un autre dossier : `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`**

```text
$ cd /tmp
$ maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
$ maintai-predict 45 1.5 40 3000
Probabilité de panne : 0 % (normal)
$ maintai-predict --version
maintai 0.2.0
$ python -c "import maintai; print(maintai.__file__)"
…/tp/tp4/Wenn_BOUKA/maintai/__init__.py
```

La commande marche depuis n'importe quel dossier, et `maintai.__file__` désigne **mon dossier de travail**, pas `site-packages`. En mode éditable, pip ne copie pas le code : il dépose dans le `site-packages` du `.venv` un lien vers les sources. J'y trouve :

```text
__editable__.maintai-0.2.0.pth
__editable___maintai_0_2_0_finder.py
maintai-0.2.0.dist-info
```

Python trouve donc `maintai` par ce *finder*, quel que soit le dossier courant. Le modèle est trouvé aussi, car `config.py` calcule les chemins à partir de `__file__`, donc vers `tp/tp4/Wenn_BOUKA/models/`.

**Modifier le message de `maintai/cli.py`, relancer sans réinstaller : le changement est-il visible ?**

Oui. En remplaçant « Probabilité de panne : » par « Risque de panne estimé : », la commande affiche aussitôt :

```text
Risque de panne estimé : 95 % (ALERTE)
```

Le script `maintai-predict` ne contient qu'un appel à `maintai.cli:main`, et ce module est lu dans mes sources à chaque exécution. Il ne faut réinstaller que si l'on modifie `pyproject.toml` (nouvelle dépendance, nouvelle commande), car les métadonnées et le script sont générés à l'installation. Le message d'origine a été remis ensuite.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `python -m build` puis du contenu de `dist` :

```text
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl

$ ls -l dist
-rw-r--r-- 1 11765 maintai-0.2.0-py3-none-any.whl
-rw-r--r-- 1 12499 maintai-0.2.0.tar.gz
```

**Contenu du wheel. Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?**

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
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Ni `models/`, ni `tests/`, ni `ui/`, ni `web/`, ni `data/`. La ligne `include = ["maintai*"]` de `[tool.setuptools.packages.find]` ne fait entrer que `maintai/` et `maintai/api/`. C'est voulu : le wheel livre **du code**. Les tests servent au développement, l'interface Streamlit est une application à part, et le modèle est un **artefact** produit par l'entraînement, régénérable et qui évolue à son propre rythme. Dans `dist-info`, `entry_points.txt` déclare la commande :

```text
[console_scripts]
maintai-predict = maintai.cli:main
```

et `METADATA` reprend mes dépendances (`Requires-Dist: scikit-learn>=1.4`, …, et `fastapi>=0.115; extra == "api"`).

**Dans un environnement neuf (`/tmp/essai`), installer le wheel et lancer `maintai-predict` :**

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : /tmp/essai/.venv/lib/python3.13/site-packages/models/model.joblib` puis `Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR.` (code de sortie 1) |
| avec `MAINTAI_MODELS_DIR` vers mes `models` | trois `InconsistentVersionWarning: Trying to unpickle estimator StandardScaler / LogisticRegression / Pipeline from version 1.8.0 when using version 1.9.1. This might lead to breaking code or invalid results. Use at your own risk.` puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement |

Changements effectués : `export MAINTAI_MODELS_DIR=…/tp/tp4/Wenn_BOUKA/models` (Windows : `set MAINTAI_MODELS_DIR=…`), puis `pip install scikit-learn==1.8.0`.

Le premier essai montre que le package installé cherche le modèle **à côté de son code**, dans `site-packages`, où il n'est pas. Le message d'erreur dit où il a cherché et quoi faire : c'est ce qui rend la panne réparable sans lire le code.

**D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?**

Le wheel demande `scikit-learn>=1.4` : dans l'environnement neuf, pip a pris la **dernière** version, 1.9.1. Or `model.joblib` est un pickle d'objets scikit-learn (le `StandardScaler`, la `LogisticRegression` et le `Pipeline` qui les enchaîne), écrit avec la version 1.8.0 du `.venv` d'entraînement. Les attributs internes d'un estimateur peuvent changer entre deux versions ; scikit-learn prévient donc que le résultat n'est pas garanti. La ligne qui l'explique :

```json
"sklearn_version": "1.8.0"
```

Avec `scikit-learn==1.8.0`, la version figée de `requirements.txt`, l'avertissement disparaît. Ici la prédiction était identique (95 %), mais rien ne le garantissait.

## 4. Questions de compréhension

**1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?**  
`dependencies` est le **contrat du package** : des versions minimales (`>=`), assez souples pour que `maintai` s'installe à côté d'autres packages sans conflit. `requirements.txt` **fige un environnement** : des versions exactes (`==`), celles avec lesquelles le modèle a été entraîné, pour le reproduire à l'identique. Il contient aussi les outils (pytest, streamlit, fastapi, build) qui ne sont pas des dépendances du package. L'expérience du wheel montre pourquoi il faut les deux : `>=1.4` laisse passer 1.9.1, `==1.8.0` relit le modèle sans risque.

**2. Quelle différence entre `pip install -e .` et `pip install dist/maintai-0.2.0-py3-none-any.whl` ?**  
`-e .` installe un **lien** vers les sources : toute modification du code est visible immédiatement. Il sert à **développer**. Le wheel est une **archive figée** de la version 0.2.0 : pip en **copie** le contenu dans `site-packages`, sans dépendre du dossier du projet, de Git ni des tests. Il sert à **livrer** (à un collègue, sur un serveur). Une modification du code n'y apparaît qu'après reconstruction et réinstallation.

**3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict` ?**  
C'est l'association d'un nom de commande à une fonction Python, au format `commande = "module:fonction"` (ici `maintai-predict = "maintai.cli:main"`). À l'installation, pip génère un petit lanceur qui importe `maintai.cli`, appelle `main()` et renvoie son code de sortie. Il le place dans le dossier des exécutables du `.venv` actif : `.venv/bin/maintai-predict` sous Linux (je l'ai trouvé avec `which maintai-predict`), `.venv\Scripts\maintai-predict.exe` sous Windows. Ce dossier n'est dans le `PATH` que si le `.venv` est activé, d'où le « command not found » quand on l'oublie.

Décision de packaging : [`docs/adr/005-package.md`](docs/adr/005-package.md).

## 5. Le rendu Git

- **Mon dossier :** `tp/tp4/Wenn_BOUKA/` (projet complet, `pyproject.toml`, ce compte rendu)
- **Branche :** `tp-wenn-bouka`, pull request vers `main`
- **`git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ?** Non : le `.gitignore` du dossier exclut `dist/`, `build/`, `*.egg-info/`, `.venv/`, `models/`, `data/*.csv` et `.env`. Le wheel se reconstruit avec `python -m build`, il n'a pas sa place dans Git.

## 6. Ce qui reste flou

- **Livrer le modèle avec le code.** Le wheel ne contient pas le modèle, et l'utilisateur doit renseigner `MAINTAI_MODELS_DIR`. Je ne sais pas encore s'il vaut mieux publier le modèle à part (stockage d'artefacts, registre de modèles comme MLflow) avec une version liée à celle du package, ou l'inclure comme *package data*.
- **Garantir la bonne version de scikit-learn sans figer `==` dans le package.** Une piste : vérifier `sklearn_version` de `model_info.json` au chargement dans `Predictor.load` et refuser de prédire en cas d'écart, plutôt que de compter sur un avertissement que personne ne lit.
