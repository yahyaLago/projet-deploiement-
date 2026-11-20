# ADR 005 : livrer MaintAI comme un package Python

Date : 20/11/2026 · Auteur : Wenn BOUKA

## Contexte

Un collègue veut une prédiction depuis son terminal sans cloner le dépôt ni lancer l'API. Il faut un livrable installable par `pip`, qui ne contienne que ce qui sert à l'exécution, et qui reste compatible avec le modèle entraîné.

## Options étudiées

1. **Partager le dépôt + `requirements.txt`.** Simple, mais le collègue récupère les tests, l'interface et l'historique Git, et doit lancer `python -m ...` depuis le bon dossier.
2. **Un package (`pyproject.toml`) distribué en wheel**, avec une commande `maintai-predict`. Installation en une ligne, utilisable depuis n'importe quel dossier.
3. **Une image Docker** contenant code + modèle. Plus robuste pour un serveur, mais disproportionné pour une commande de terminal à ce stade.

## Décision

Option 2. `dependencies` ne liste que les imports réels de `maintai/` hors API (numpy, pandas, scikit-learn, joblib, httpx), en versions minimales ; l'API, l'interface et les outils de développement sont dans les groupes optionnels `api`, `ui` et `dev`. Seul le dossier `maintai/` entre dans le wheel. Le modèle reste en dehors et se désigne avec `MAINTAI_MODELS_DIR`.

## Conséquences

- `pip install -e .` pour développer, `python -m build` puis installation du wheel pour livrer.
- Le modèle n'est pas dans le wheel : la commande doit dire où elle l'a cherché (c'est le cas).
- `scikit-learn>=1.4` peut installer une version plus récente que celle du modèle (1.9.1 contre 1.8.0 dans mon essai) : il faut installer les versions de `requirements.txt`, ou à terme vérifier `sklearn_version` au chargement.
