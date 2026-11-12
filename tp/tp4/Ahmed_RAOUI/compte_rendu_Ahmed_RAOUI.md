# Compte rendu · TP4 : MaintAI devient un package Python

**Auteur :** Ahmed RAOUI  
**Groupe :** G1My  
**Date :** 12/11/2026

> Compte rendu individuel. Les résultats ci-dessous proviennent des manipulations réalisées pendant le TP4. Les vérifications non encore effectuées sont explicitement signalées.

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

J'ai créé et activé un environnement virtuel propre au TP4 :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

J'ai ensuite installé le package et les dépendances nécessaires aux tests :

```powershell
python -m pip install -e .
python -m pip install -e ".[api,ui,dev]"
python -m pytest -v
```

**Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :**

Ce test initial précis n'a pas été relevé dans ma séance : j'ai exécuté la suite après l'installation du package et de ses dépendances optionnelles.

**Quels sont les deux tests qui échouent, et pourquoi ?**

Le modèle du professeur prévoit deux tests initialement en échec à corriger durant le Sprint 1. Je ne peux pas en donner les noms exacts à partir de mes propres sorties, car je n'ai pas conservé un résultat de tests à ce stade. En revanche, après configuration de `pyproject.toml`, les tests de packaging (`tests/test_package.py`) et les autres tests passent.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

**Vos sections `dependencies` et `[project.scripts]` :**

```toml
# Dans [project]
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

J'ai aussi renseigné la description du package, sans supprimer les commentaires `TODO` du professeur.

**Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?**

`pytest` sert à exécuter les tests : il fait partie des dépendances optionnelles `dev`. `fastapi` est nécessaire à l'API, mais pas à une prédiction lancée directement par la CLI : il figure dans le groupe optionnel `api`. Cela évite d'imposer ces outils à toute installation minimale du package.

**Sortie de `pip show maintai` (les quatre premières lignes) :**

Commande non exécutée pendant la séance ; à compléter avec la sortie réelle :

```powershell
python -m pip show maintai
```

L'installation réalisée avec `python -m pip install -e .` a affiché `Successfully installed maintai-0.2.0`.

**Dernière ligne de `python -m pytest` à la fin du sprint 1 :**

```text
27 passed, 1 warning in 13.83s
```

L'avertissement concerne une dépréciation dans `fastapi.testclient` / Starlette ; il n'empêche pas la réussite des tests.

**Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?**

Pendant le Sprint 1, depuis le projet et après entraînement du modèle, j'ai obtenu :

```text
Probabilité de panne : 95 % (ALERTE)
```

La vérification précise de `maintai.__file__` en mode editable n'a pas été effectuée. En installation editable, Python référence le code du dossier source `maintai/` du projet, plutôt qu'une copie indépendante du package. Pour vérifier le chemin exact :

```powershell
python -c "import maintai; print(maintai.__file__)"
```

**Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?**

Manipulation non réalisée. En principe, une installation `pip install -e .` permet de voir les modifications du code Python source sans réinstallation, car elle pointe vers le projet de développement. Ce comportement reste à vérifier expérimentalement pour cet exercice.

## 3. Sprint 2 : construire et installer le wheel

**Sortie de `dir dist` après `python -m build` :**

Le build a réussi et a produit :

```text
dist/maintai-0.2.0-py3-none-any.whl
dist/maintai-0.2.0.tar.gz
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl
```

**Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?**

D'après le journal de construction, le Wheel contient notamment les modules `maintai/__init__.py`, `maintai/cli.py`, `maintai/client.py`, `maintai/config.py`, `maintai/data.py`, `maintai/dataset.py`, `maintai/predict.py`, `maintai/train.py`, `maintai/api/` et les métadonnées `maintai-0.2.0.dist-info/`. La commande `tar -tf` n'a pas été exécutée séparément.

Le modèle entraîné (`models/model.joblib`), les tests et `ui/` ne sont pas inclus dans ce Wheel : la configuration `[tool.setuptools.packages.find]` ne sélectionne que `maintai*`. Le modèle doit être fourni séparément.

**Dans un environnement neuf, installez le wheel et lancez `maintai-predict` :**

J'ai créé et activé l'environnement indépendant `tp4-test-venv`, puis installé le Wheel :

```powershell
python -m pip install .\dist\maintai-0.2.0-py3-none-any.whl
maintai-predict --version
```

La commande de version a retourné `maintai 0.2.0`. Ensuite, je me suis placé dans `C:\Users\Cloud`, hors du dossier TP4.

| Étape | Ce qui s'affiche |
|---|---|
| Sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : ...\site-packages\models\model.joblib` ; l'application demande d'entraîner le modèle ou de renseigner `MAINTAI_MODELS_DIR`. |
| Avec `MAINTAI_MODELS_DIR` vers mes `models` | `Probabilité de panne : 95 % (ALERTE)` |
| Après `pip install scikit-learn==1.8.0` | Essai non effectué pendant la séance ; résultat à relever si demandé. |

Configuration utilisée pour retrouver le modèle :

```powershell
$env:MAINTAI_MODELS_DIR = "C:\Users\Cloud\Downloads\projet-deploiement-\tp\tp4\models"
maintai-predict 72 6 85 15000
```

**D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?**

Cet avertissement peut apparaître lorsqu'un modèle enregistré avec une version de scikit-learn est rechargé sous une version différente. Le fichier `models/model_info.json`, généré par `maintai/train.py`, contient la clé `"sklearn_version"` indiquant la version utilisée pour entraîner le modèle. Pour donner sa valeur exacte, il faut ouvrir ce fichier local. Je n'ai pas effectué ici le test de changement forcé de version.

## 4. Questions de compréhension

1. **Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?**  
   `requirements.txt` sert à reproduire un environnement d'exécution, souvent avec des versions fixées. `dependencies` dans `pyproject.toml` décrit les dépendances minimales nécessaires au package lors de son installation. Elles sont lues automatiquement par `pip` lorsqu'on installe le package ou son Wheel.

2. **Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?**  
   `pip install -e .` installe le projet en mode développement : le code exécuté reste lié au répertoire source. L'installation d'un Wheel installe une distribution construite du package dans l'environnement Python ; les modifications ultérieures du dossier source n'y sont pas automatiquement répercutées.

3. **Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?**  
   Un point d'entrée associe une commande terminal à une fonction Python. Ici, `maintai-predict = "maintai.cli:main"` invoque `main()` dans `maintai/cli.py`. Sous Windows, pip crée le lanceur `maintai-predict.exe` dans le dossier `Scripts` de l'environnement virtuel actif (par exemple `.venv\Scripts\`).

## 5. Le rendu Git

- **Lien de la pull request :** à renseigner après ouverture de la PR du TP4.
- **Le tag `tp4` existe sur GitHub :** non vérifié à ce stade ; coordination nécessaire avec le modérateur du groupe.
- **`git status` avant le commit :** le premier `git status --short --branch` affichait `?? ./` pour les nouveaux fichiers du TP4. Les répertoires `dist/`, `build/`, `.venv/`, `models/` et `*.egg-info/` figurent dans le `.gitignore` du TP4. Une vérification finale de `git status` est nécessaire avant de créer le commit.
- **Organisation du rendu :** dossier personnel `tp/tp4/Ahmed_RAOUI/` avec code source, tests, `pyproject.toml` et compte rendu individuel. Les fichiers temporaires, environnements virtuels et artefacts générés restent exclus.

## 6. Ce qui reste flou

Le principal point de vigilance est la **portabilité du modèle** : installer le Wheel suffit à rendre la commande disponible, mais pas à fournir automatiquement `model.joblib`. Il faut distribuer le modèle séparément et renseigner `MAINTAI_MODELS_DIR`. Il reste aussi à observer concrètement l'avertissement de compatibilité scikit-learn en testant un chargement avec une version différente, puis à finaliser la Pull Request et le tag du groupe.
