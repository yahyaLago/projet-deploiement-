# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** …  ·  **Membres :** Yahya BAID  ·  **Date :** 12/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
FAILED tests/test_package.py::test_installed_version_matches_the_code - importlib.metadata.PackageNotFoundError: No package metadata was found for maintai
FAILED tests/test_package.py::test_command_is_declared - AssertionError: assert 'maintai-predict' in [...]
2 failed, 25 passed, 1 warning
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` :

- `test_installed_version_matches_the_code` : il appelle `importlib.metadata.version("maintai")`, qui lit les métadonnées d'un package **installé**. À ce stade, `maintai` est seulement un dossier importable depuis `TP\TP4` (le répertoire courant est dans `sys.path`), mais pip ne l'a jamais installé : aucune métadonnée n'existe, d'où `PackageNotFoundError`.
- `test_command_is_declared` : il cherche `maintai-predict` parmi les points d'entrée `console_scripts` de l'environnement. La section `[project.scripts]` n'était pas encore écrite et le package n'était pas installé, donc la commande n'existe pas.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

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

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` contient uniquement ce dont le code de `maintai/` a besoin pour fonctionner chez n'importe quel utilisateur (le collègue qui lance `maintai-predict` n'a besoin que de pandas, scikit-learn, joblib…). `pytest` ne sert qu'aux développeurs pour tester : il est dans le groupe optionnel `dev`. `fastapi` (et `uvicorn`) ne servent qu'à faire tourner l'API : ils sont dans le groupe `api`, installable avec `pip install maintai[api]`. Les mettre dans `dependencies` alourdirait l'installation et augmenterait les risques de conflits de versions pour quelqu'un qui veut seulement la commande.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Package Python de maintenance prédictive permettant d'estimer le risque de panne des machines à partir de données de capteurs
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
> cd /d %TEMP%
> maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
> python -c "import maintai; print(maintai.__file__)"
...\TP\TP4\maintai\__init__.py
```

La commande fonctionne depuis n'importe quel dossier, et `maintai.__file__` pointe toujours vers **notre dossier de travail `TP\TP4\maintai\`**, pas vers `site-packages`. Avec `pip install -e .` (mode éditable), pip ne copie pas le code : il ajoute dans le `site-packages` du `.venv` un lien (un fichier `.pth` / un finder éditable) qui renvoie vers le dossier du projet. Python trouve donc `maintai` via ce lien, quel que soit le répertoire courant. Le modèle est trouvé aussi, car `config.py` calcule `ROOT` à partir de `__file__`, donc `TP\TP4\models\`.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui. En remplaçant « Probabilité de panne : » par « Risque de panne estimé : », la commande affiche immédiatement `Risque de panne estimé : 95 % (ALERTE)` sans relancer `pip install`. C'est le principe du mode éditable : le `.exe` `maintai-predict` appelle simplement `maintai.cli:main`, et ce module est lu directement dans nos fichiers sources à chaque exécution. On réinstalle seulement si l'on modifie `pyproject.toml` (nouvelle dépendance, nouvelle commande), car les métadonnées et le `.exe` sont créés à l'installation. (Le message d'origine a été remis ensuite.)

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl

> dir dist
12/11/2026  11:41            11 649 maintai-0.2.0-py3-none-any.whl
12/11/2026  11:41            12 708 maintai-0.2.0.tar.gz
               2 fichier(s)           24 357 octets
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
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

Non : ni le modèle (`models/`), ni `tests/`, ni `ui/`, ni `web/`, ni `data/` ne sont dans le wheel. La ligne `[tool.setuptools.packages.find] include = ["maintai*"]` ne fait entrer que le package `maintai/` (et `maintai/api/`). C'est voulu : le wheel livre **le code**. Les tests servent au développement, l'interface Streamlit est une application séparée, et le modèle est un artefact produit par l'entraînement (lourd, régénérable, versionné à part). Le dossier `maintai-0.2.0.dist-info/` contient les métadonnées, dont `entry_points.txt` qui déclare la commande `maintai-predict`.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : %TEMP%\essai\.venv\Lib\site-packages\models\model.joblib` puis « Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR. » |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | `InconsistentVersionWarning: Trying to unpickle estimator Pipeline from version 1.8.0 when using version 1.9.1. This might lead to breaking code or invalid results. Use at your own risk.` puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement |

Changements effectués : `set MAINTAI_MODELS_DIR=<chemin>\TP\TP4\models`, puis `pip install scikit-learn==1.8.0`.

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Le wheel déclare `scikit-learn>=1.4` : dans l'environnement neuf, pip a installé la **dernière** version disponible (1.9.1). Or le modèle `model.joblib` est un objet scikit-learn sérialisé (pickle) avec la version 1.8.0 du `.venv` du TP4. Au chargement, scikit-learn détecte que l'objet a été écrit par une autre version et prévient que le résultat pourrait être faux ou planter (les attributs internes des estimateurs peuvent changer d'une version à l'autre). La ligne qui l'explique :

```json
"sklearn_version": "1.8.0"
```

En installant exactement `scikit-learn==1.8.0` (la version de `requirements.txt`), l'avertissement disparaît.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `dependencies` déclare des versions **minimales** (`>=`) : c'est le contrat du package, assez souple pour qu'il puisse s'installer à côté d'autres packages sans conflit. `requirements.txt` fige des versions **exactes** (`==`) : il reproduit à l'identique l'environnement dans lequel le modèle a été entraîné, ce qui est indispensable pour relire `model.joblib` sans risque. Il contient aussi les outils (pytest, streamlit, fastapi, build) qui ne font pas partie des dépendances du package.

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `pip install -e .` installe en mode éditable : pip crée un lien vers le dossier source, chaque modification du code est visible immédiatement. C'est pour **développer**. Le wheel est une archive figée du code à la version 0.2.0 : pip **copie** les fichiers dans `site-packages`, sans lien avec nos sources ni besoin du projet, de Git ou des tests. C'est pour **livrer** (à un collègue, sur un serveur). Une modification du code n'y apparaît qu'après avoir reconstruit et réinstallé le wheel.

3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   Un point d'entrée associe un nom de commande à une fonction Python, au format `commande = "module:fonction"` (ici `maintai-predict = "maintai.cli:main"`). À l'installation, pip génère un petit exécutable qui importe `maintai.cli` et appelle `main()`, puis retourne son code de sortie. Sous Windows, pip le crée dans le dossier `Scripts` de l'environnement actif : `TP\TP4\.venv\Scripts\maintai-predict.exe` (et `%TEMP%\essai\.venv\Scripts\maintai-predict.exe` pour l'environnement neuf). Ce dossier est dans le `PATH` quand le `.venv` est activé, d'où le message « n'est pas reconnu » si l'on oublie l'activation ou si l'on a déclaré la commande après l'installation.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? non (le `.gitignore` du starter exclut `dist/`, `build/`, `*.egg-info/`, `.venv/` et `models/` : le wheel se reconstruit avec `python -m build`, il ne va pas dans Git)

## 6. Ce qui reste flou

- Comment livrer proprement le modèle avec le code en production : faut-il le publier à part (stockage d'artefacts, registre de modèles) avec un numéro de version lié à celui du package, ou l'intégrer au wheel via des *package data* ?
- Comment garantir la bonne version de scikit-learn chez l'utilisateur sans figer `==` dans `pyproject.toml` (par exemple un fichier de contraintes livré avec le modèle, ou une vérification de `sklearn_version` au chargement qui refuse de prédire).
