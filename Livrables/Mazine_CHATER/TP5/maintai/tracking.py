"""Suivi des entraînements avec MLflow.

Chaque entraînement devient un « run » qui garde ses paramètres, l'empreinte
des données, ses métriques et le modèle. Les runs sont stockés dans
`mlflow.db` et `mlruns/`, que l'on explore avec `mlflow ui`.
"""
import hashlib
import os
from pathlib import Path

# Coupe un message d'information de MLflow qui n'apporte rien ici.
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
import mlflow.sklearn

EXPERIMENT = "maintai"

# Le format skops refuse les types qu'il ne connaît pas. Les arbres de la
# forêt aléatoire sont explicitement déclarés sûrs.
TYPES_DE_CONFIANCE = ["sklearn.tree._tree.Tree"]


def file_md5(path: Path) -> str:
    """Empreinte MD5 du fichier de données, celle que DVC écrit dans le .dvc."""
    with path.open("rb") as fichier:
        return hashlib.file_digest(fichier, "md5").hexdigest()


def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement complet et renvoie l'identifiant du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TYPES_DE_CONFIANCE,
        )
    return run.info.run_id
