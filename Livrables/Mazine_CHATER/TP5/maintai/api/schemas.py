"""Schémas d'entrée et de sortie de l'API, validés par Pydantic."""
from pydantic import BaseModel, ConfigDict, Field


class SensorReading(BaseModel):
    """Un relevé de capteurs envoyé par un client."""

    model_config = ConfigDict(
        extra="forbid",  # un champ inconnu est une erreur, pas un détail ignoré
        json_schema_extra={
            "examples": [
                {
                    "temperature_c": 72.5,
                    "vibration_mm_s": 6.1,
                    "load_pct": 85.0,
                    "runtime_hours": 15000,
                }
            ]
        },
    )

    temperature_c: float = Field(ge=-40, le=150, description="Température du moteur (°C)")
    vibration_mm_s: float = Field(ge=0, le=50, description="Vitesse de vibration (mm/s)")
    load_pct: float = Field(ge=0, le=100, description="Charge (% de la capacité nominale)")
    runtime_hours: float = Field(
        ge=0, le=100_000, description="Heures de fonctionnement cumulées"
    )


class PredictionOut(BaseModel):
    """Réponse de l'API pour un relevé."""

    failure_probability: float = Field(
        description="Probabilité estimée de panne, entre 0 et 1"
    )
    alert: bool = Field(description="Vrai si la probabilité atteint le seuil")
    threshold: float = Field(description="Seuil d'alerte utilisé")
    model_version: str = Field(description="Date d'entraînement du modèle")


class HealthOut(BaseModel):
    """État du service, utile pour la supervision."""

    status: str
    model_loaded: bool
