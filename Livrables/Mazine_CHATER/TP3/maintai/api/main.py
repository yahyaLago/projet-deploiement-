"""API HTTP de MaintAI : expose le modèle de prédiction de panne.

Lancement : uvicorn maintai.api.main:app --reload --env-file .env
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from maintai import __version__
from maintai.api.schemas import HealthOut, PredictionOut, SensorReading
from maintai.api.security import require_api_key
from maintai.config import get_settings
from maintai.predict import Predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Le modèle est chargé une seule fois, au démarrage, et non à chaque requête.
    try:
        app.state.predictor = Predictor.load(get_settings())
    except FileNotFoundError:
        # L'API démarre quand même : /health et /v1/predict signaleront l'absence.
        app.state.predictor = None
    yield
    app.state.predictor = None


app = FastAPI(
    title="MaintAI API",
    version=__version__,
    description="Prédiction de panne à partir de relevés de capteurs.",
    lifespan=lifespan,
)

# Seules les pages autorisées peuvent appeler l'API depuis un navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# La clé API protège toutes les routes sous /v1 ; /health reste public.
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


@app.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    """Route publique : dit si le service est prêt à prédire."""
    return HealthOut(
        status="ok",
        model_loaded=getattr(request.app.state, "predictor", None) is not None,
    )


@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading, request: Request) -> PredictionOut:
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))


app.include_router(router)
