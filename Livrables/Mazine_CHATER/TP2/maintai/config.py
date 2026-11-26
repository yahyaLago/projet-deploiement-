"""Configuration de MaintAI : chemins, seuil et sécurité, lus dans l'environnement.

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

ORIGINES_PAR_DEFAUT = "http://localhost:5500,http://127.0.0.1:5500"


@dataclass(frozen=True)
class Settings:
    """Chemins et paramètres partagés par l'API et l'entraînement."""

    data_path: Path
    models_dir: Path
    threshold: float
    api_key: str | None = None
    cors_origins: tuple[str, ...] = ()

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


def _liste(variable: str, default: str) -> tuple[str, ...]:
    """Transforme une liste séparée par des virgules en tuple propre."""
    return tuple(
        element.strip()
        for element in os.getenv(variable, default).split(",")
        if element.strip()
    )


def get_settings() -> Settings:
    """Lit l'environnement au moment de l'appel, jamais mis en cache."""
    return Settings(
        data_path=_path("MAINTAI_DATA_PATH", RACINE / "data" / "sensors.csv"),
        models_dir=_path("MAINTAI_MODELS_DIR", RACINE / "models"),
        threshold=float(os.getenv("MAINTAI_THRESHOLD", "0.3")),
        api_key=os.getenv("MAINTAI_API_KEY") or None,
        cors_origins=_liste("MAINTAI_CORS_ORIGINS", ORIGINES_PAR_DEFAUT),
    )
