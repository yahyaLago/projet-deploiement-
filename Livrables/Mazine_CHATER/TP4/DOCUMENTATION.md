# Documentation — TP4

## Le problème

Jusqu'ici, le code ne fonctionnait que depuis la racine du projet, avec
`python -m maintai...`. Impossible de l'importer depuis un autre dossier,
et aucun collègue ne peut l'installer sans copier les fichiers à la main.

Le TP4 répond à trois questions :

1. Quelles bibliothèques le code utilise-t-il vraiment ?
2. Comment installer le projet comme un paquet normal ?
3. Comment exposer une commande dans le terminal ?

## Le fichier `pyproject.toml`

C'est la fiche d'identité du paquet. Il est lu par `pip install` et par
`python -m build`.

| Section | Rôle |
|---|---|
| `[build-system]` | indique à pip comment construire le paquet (setuptools) |
| `[project]` | nom, description, version, dépendances obligatoires |
| `[project.optional-dependencies]` | groupes `api`, `ui`, `dev` |
| `[project.scripts]` | crée la commande `maintai-predict` |
| `[tool.setuptools.dynamic]` | lit la version dans `maintai/__init__.py` |
| `[tool.setuptools.packages.find]` | n'embarque que `maintai*` |

Séparer les dépendances est important : un utilisateur qui veut seulement la
bibliothèque n'a pas besoin d'installer FastAPI ni Streamlit.

## Version unique

La version n'est écrite qu'à un seul endroit : `maintai/__init__.py`. Le
`pyproject.toml` la lit dynamiquement. On évite ainsi le classique « le
paquet annonce 0.2.0 mais le code dit 0.1.0 ».

## De `python -m` à une commande

`maintai-predict = "maintai.cli:main"` demande à pip de créer un petit
exécutable qui appelle `main()`. La fonction renvoie un code de sortie :

- `0` : prédiction affichée ;
- `1` : modèle introuvable.

Un script qui renvoie un code correct peut être utilisé dans une chaîne
d'automatisation : `maintai-predict ... || echo "échec"`.

## Mode éditable

`pip install -e .` installe un lien vers le dossier courant, pas une copie.
Modifier le code est immédiatement pris en compte. C'est le mode adapté au
développement ; `pip install .` installe une copie figée.

## Le modèle n'est pas dans le paquet

Un paquet Python doit rester petit et reproductible. Le modèle dépend des
données et de leur version : il n'a pas sa place dans un wheel. Le code lit
son emplacement dans `MAINTAI_MODELS_DIR` et affiche un message clair s'il
est absent.

## Limites

- Il n'y a pas encore de publication sur un index (PyPI privé ou public).
- Le paquet ne déclare pas de licence.
- La compatibilité est testée sur une seule version de Python.
