"""Entraînement, évaluation, sauvegarde et suivi MLflow.

    python -m maintai.train
    python -m maintai.train --model forest
    python -m maintai.train --C 0.1 --threshold 0.2
"""
import argparse
import json
import sys
from datetime import UTC, datetime

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from maintai.config import FEATURES, SEED, TARGET, Settings, get_settings
from maintai.data import load_data, split
from maintai.tracking import log_run


def build_model(kind: str = "logreg", C: float = 1.0) -> Pipeline:
    """Le prétraitement est dans le pipeline : il sera sauvegardé avec le modèle."""
    if kind == "forest":
        classifieur = RandomForestClassifier(n_estimators=200, random_state=SEED)
    else:
        classifieur = LogisticRegression(C=C, max_iter=1000)
    return Pipeline([
        ("normalisation", StandardScaler()),
        ("classifieur", classifieur),
    ])


def evaluate(model, X_test, y_test, threshold: float) -> dict:
    """Évalue au seuil d'alerte choisi, et non au 0,5 par défaut de scikit-learn."""
    probabilites = model.predict_proba(X_test)[:, 1]
    predictions = (probabilites >= threshold).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 3),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 3),
        "threshold": threshold,
    }


def evaluate_baseline(X_train, y_train, X_test, y_test) -> dict:
    """Référence volontairement naïve : toujours prédire la classe majoritaire."""
    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    predictions = baseline.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 3),
    }


def save(model, metrics: dict, settings: Settings, threshold: float) -> None:
    """Écrit le modèle, son contrat d'entrée et ses métriques sur le disque."""
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.model_path)

    info = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": threshold,
        "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sklearn_version": sklearn.__version__,
    }
    settings.info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    settings.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m maintai.train")
    parser.add_argument("--model", choices=["logreg", "forest"], default="logreg")
    parser.add_argument(
        "--C", type=float, default=1.0, help="régularisation de la régression logistique"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="seuil d'alerte (défaut : MAINTAI_THRESHOLD)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict:
    args = parse_args(argv or [])
    settings = get_settings()
    threshold = args.threshold if args.threshold is not None else settings.threshold

    df = load_data(settings.data_path)
    X_train, X_test, y_train, y_test = split(df)

    model = build_model(args.model, args.C).fit(X_train, y_train)
    metrics = {
        "model": evaluate(model, X_test, y_test, threshold),
        "baseline": evaluate_baseline(X_train, y_train, X_test, y_test),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    save(model, metrics, settings, threshold)

    params = {"model": args.model, "threshold": threshold, "n_train": len(X_train)}
    if args.model == "logreg":
        params["C"] = args.C
    metriques_du_run = {
        nom: valeur for nom, valeur in metrics["model"].items() if nom != "threshold"
    } | {"baseline_recall": metrics["baseline"]["recall"]}
    run_id = log_run(
        params=params,
        metrics=metriques_du_run,
        model=model,
        X_example=X_train.head(3),
        data_path=settings.data_path,
    )

    print(json.dumps(metrics, indent=2))
    print(f"Modèle sauvegardé dans {settings.model_path}")
    print(f"Run MLflow : {run_id}")
    return metrics


if __name__ == "__main__":
    main(sys.argv[1:])
