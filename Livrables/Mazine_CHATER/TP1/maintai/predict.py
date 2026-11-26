"""Chargement du modèle sérialisé et calcul d'une prédiction."""
import json
from dataclasses import dataclass

import joblib
import pandas as pd

from maintai.config import Settings


@dataclass(frozen=True)
class Predictor:
    """Modèle chargé, avec son contrat d'entrée et son seuil d'alerte."""

    model: object
    features: list[str]
    threshold: float
    version: str

    @classmethod
    def load(cls, settings: Settings) -> "Predictor":
        """Reconstruit un prédicteur depuis le disque.

        Lève FileNotFoundError si le modèle n'a pas encore été entraîné.
        """
        model = joblib.load(settings.model_path)
        info = json.loads(settings.info_path.read_text(encoding="utf-8"))
        return cls(
            model=model,
            features=info["features"],
            threshold=info["threshold"],
            version=info["trained_at"],
        )

    def predict(self, reading: dict) -> dict:
        """Renvoie la probabilité de panne, l'alerte et la version du modèle."""
        # Les colonnes doivent être celles de l'entraînement, dans le même ordre.
        X = pd.DataFrame([reading])[self.features]
        probabilite = float(self.model.predict_proba(X)[0, 1])
        return {
            "failure_probability": round(probabilite, 4),
            "alert": probabilite >= self.threshold,
            "threshold": self.threshold,
            "model_version": self.version,
        }
