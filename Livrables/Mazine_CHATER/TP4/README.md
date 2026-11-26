# MaintAI — TP4

Le TP4 transforme le projet en package Python installable. Après
`pip install -e .`, le code s'importe depuis n'importe quel dossier et la
commande `maintai-predict` est disponible dans le terminal.

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Utilisation

```bash
python -m maintai.dataset
python -m maintai.train
maintai-predict 72 6 85 15000
maintai-predict --version
```

La commande affiche la probabilité de panne et l'état de l'alerte. Si le
modèle n'est pas entraîné, elle indique le chemin cherché et renvoie le code
de sortie 1.

## Construire une distribution

```bash
python -m build
```

Le fichier produit dans `dist/` contient le code, pas le modèle. Sur une
autre machine, il faut fournir les artefacts via `MAINTAI_MODELS_DIR`.

## Ce que déclare `pyproject.toml`

- les dépendances strictement nécessaires au code (`numpy`, `pandas`,
  `scikit-learn`, `joblib`, `httpx`) ;
- des groupes optionnels pour l'API (`fastapi`, `uvicorn`), l'interface
  (`streamlit`) et le développement (`pytest`, `ruff`) ;
- la version, lue dans `maintai/__init__.py` ;
- la commande `maintai-predict`, point d'entrée vers `maintai.cli:main` ;
- les paquets à inclure : uniquement `maintai*`, pas les tests ni les
  données.

## Tests

```bash
pytest
```

Deux tests vérifient l'installation : la version installée correspond au
code, et la commande `maintai-predict` est bien déclarée.

Les choix techniques sont détaillés dans `DOCUMENTATION.md`.
