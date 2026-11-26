"""Configuration de MaintAI : chemins et seuil, lus dans l'environnement.

Aucun chemin n'est figé dans le code : les tests et les déploiements peuvent
changer de fichier de données ou de dossier de modèles par variable
d'environnement. `get_settings()` relit donc la configuration à chaque appel.
"""
import os
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Contrat d'entrée du modèle : ces colonnes, dans cet ordre.
FEATURES = ["temperature_c", "vibration_mm_s", "load_pct", "runtime_hours"]
TARGET = "failure"
SEED = 42


@dataclass(frozen=True)
class Settings:
    """Chemins et paramètres partagés par l'entraînement et la prédiction."""

    data_path: Path
    models_dir: Path
    threshold: float

    @property
    def model_path(self) -> Path:
        return self.models_dir / "model.joblib"

    @property
    def info_path(self) -> Path:
        return self.models_dir / "model_info.json"

    @property
    def metrics_path(self) -> Path:
        return self.models_dir / "metrics.json"


def _path(variable: str, default: Path) -> Path:
    return Path(os.getenv(variable, str(default)))


def get_settings() -> Settings:
    """Lit l'environnement au moment de l'appel, jamais mis en cache."""
    return Settings(
        data_path=_path("MAINTAI_DATA_PATH", RACINE / "data" / "sensors.csv"),
        models_dir=_path("MAINTAI_MODELS_DIR", RACINE / "models"),
        threshold=float(os.getenv("MAINTAI_THRESHOLD", "0.3")),
    )
