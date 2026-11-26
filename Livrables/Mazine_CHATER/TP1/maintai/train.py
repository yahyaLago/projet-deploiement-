"""Entraînement du modèle, comparaison à une baseline et sauvegarde.

    python -m maintai.train
"""
import json
import sys
from datetime import UTC, datetime

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from maintai.config import FEATURES, TARGET, Settings, get_settings
from maintai.data import load_data, split


def build_model() -> Pipeline:
    """Le prétraitement est dans le pipeline : il sera sauvegardé avec le modèle."""
    return Pipeline([
        ("normalisation", StandardScaler()),
        ("classifieur", LogisticRegression(max_iter=1000)),
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


def save(model, metrics: dict, settings: Settings) -> None:
    """Écrit le modèle, son contrat d'entrée et ses métriques sur le disque."""
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.model_path)

    info = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": settings.threshold,
        "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sklearn_version": sklearn.__version__,
    }
    settings.info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    settings.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def main() -> dict:
    settings = get_settings()
    df = load_data(settings.data_path)
    X_train, X_test, y_train, y_test = split(df)

    model = build_model().fit(X_train, y_train)
    metrics = {
        "model": evaluate(model, X_test, y_test, settings.threshold),
        "baseline": evaluate_baseline(X_train, y_train, X_test, y_test),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    save(model, metrics, settings)

    print(json.dumps(metrics, indent=2))
    print(f"Modèle sauvegardé dans {settings.model_path}")
    return metrics


if __name__ == "__main__":
    main()
