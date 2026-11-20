# Compte rendu · TP1 : exposer le modèle MaintAI derrière une API

**Auteur :** Wenn BOUKA  
**Groupe :** G1  
**Date :** 20/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp1`

---

## 1. Objectif et mise en place

Le modèle de MaintAI estime la probabilité de panne d'une machine à partir de quatre mesures de capteurs. Le TP le rend appelable par n'importe quel programme : on envoie un relevé en JSON à `POST /v1/predict`, l'API renvoie la probabilité et lève une alerte dès qu'elle atteint le seuil de 0,3.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset        # 5000 relevés, taux de panne 13.6 %
python -m maintai.train          # models/model.joblib
python -m pytest
```

Avant d'écrire la moindre ligne (schéma vide, `predict()` non écrite), `pytest` donne :

```text
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'al...
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
3 failed, 10 passed, 1 warning
```

Ce qui m'a frappé, c'est que `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected` sont **déjà verts**. Ils passent pour une mauvaise raison : avec un schéma sans champ et `extra="forbid"`, *tout* relevé est refusé en 422, y compris un relevé correct. Les trois échecs le confirment : même `test_503_when_model_missing` reçoit 422 au lieu de 503, parce que la requête n'atteint jamais la fonction. Un test qui attend un refus est facile à satisfaire en refusant tout ; il faut toujours le lire à côté du test qui attend un succès.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

```python
temperature_c: float = Field(ge=-40, le=150, description="Température du moteur (°C)")
vibration_mm_s: float = Field(ge=0, le=50, description="Vitesse de vibration (mm/s)")
load_pct: float = Field(ge=0, le=100, description="Charge (% de la capacité nominale)")
runtime_hours: float = Field(ge=0, le=100_000, description="Heures de fonctionnement cumulées")
```

| Champ | Min | Max | Pourquoi cette borne |
|---|---:|---:|---|
| `temperature_c` | -40 | 150 | -40 °C couvre un démarrage à froid dans un atelier non chauffé ; au-delà de 150 °C, c'est le capteur qu'il faut soupçonner, pas le moteur. |
| `vibration_mm_s` | 0 | 50 | Une vitesse de vibration est une amplitude, jamais négative ; 50 mm/s laisse de la marge au-dessus des machines les plus dégradées. |
| `load_pct` | 0 | 100 | Pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | 0 | 100 000 | Compteur cumulé ; 100 000 h ≈ 11 ans de marche continue. |

Les bornes sont **physiques** et non copiées sur le min/max du CSV (la température y va de 23,5 à 94,5 °C). Une machine qui chauffe à 110 °C est justement celle qu'on veut évaluer : la refuser parce que le jeu d'entraînement n'a jamais vu cette valeur rendrait l'API muette au pire moment.

Avec le schéma seul, les trois échecs changent de nature :

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed, 1 warning
```

C'est un progrès : le relevé valide franchit la validation et arrive dans `predict()`.

## 3. La route de prédiction (`maintai/api/main.py`)

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

- **503 et non 500.** Un 500 dit « bug inattendu ». Ici la cause est connue et réparable : le modèle n'a pas été entraîné. 503 (*Service Unavailable*) dit « revenez plus tard », et le message donne la commande à lancer.
- **Chargement unique dans `lifespan`.** Le fichier joblib est lu une fois au démarrage et gardé dans `state`. Le relire à chaque requête ajouterait un accès disque à chaque prédiction. Si le fichier manque, l'API démarre quand même et `/health` l'annonce, ce qui permet de diagnostiquer sans boucle de plantage.

## 4. Les tests

```text
13 passed, 1 warning
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | santé, prédiction, alerte, rejet 422 (borne et champ manquant), 503, documentation OpenAPI |
| `tests/test_data.py` | 3 | génération et découpage des données |
| `tests/test_train.py` | 3 | entraînement et fichiers produits |

Avec `tests/test_casser.py` (5 cas, séance 5) et `tests/test_demo.py` (1 test), le dossier compte 19 tests, tous verts. `ruff check .` répond `All checks passed!`.

## 5. L'API en fonctionnement

```bash
uvicorn maintai.api.main:app --reload
```

| Requête | Code | Réponse |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` `{72.5, 6.1, 85, 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,...}` |
| `POST /v1/predict` `{45, 1.5, 40, 3000}` (machine saine) | 200 | `{"failure_probability":0.0001,"alert":false,"threshold":0.3,...}` |
| `POST /v1/predict` avec `temperature_c = 500` | 422 | `less_than_equal` · `Input should be less than or equal to 150` |
| `POST /v1/predict` avec `vibration_mm_s = -2` | 422 | `greater_than_equal` · `Input should be greater than or equal to 0` |
| `POST /v1/predicte` (faute de frappe) | 404 | `{"detail":"Not Found"}` |

Avec un dossier de modèles vide (`MAINTAI_MODELS_DIR` vers un dossier inexistant) :

| Requête | Code | Réponse |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":false}` |
| `POST /v1/predict` | 503 | `Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API` |

Dans `/docs`, le schéma `SensorReading` affiche pour chaque champ son type, son minimum, son maximum et sa description : la même déclaration Pydantic sert à valider et à documenter.

## 6. Questions de compréhension

**1. REST et FastAPI, quelle différence ?**  
REST est un style de conception d'API web (ressources désignées par des URL, méthodes HTTP, codes de statut, échanges en JSON). FastAPI est une bibliothèque Python pour écrire une API qui suit ce style.

**2. Les trois rôles du schéma Pydantic ?**  
Valider l'entrée (sinon 422), documenter l'API (`/docs`), et livrer à la fonction un objet Python typé déjà contrôlé.

**3. Dans `http://localhost:8000/v1/predict` ?**  
`localhost` est la machine elle-même, `8000` le port où uvicorn écoute, `/v1/predict` une route déclarée dans le code (pas un dossier sur le disque).

**4. Pourquoi `/v1` ?**  
C'est la version du contrat. Si les champs changent, on publie `/v2` à côté, et les clients restés sur `/v1` continuent de fonctionner.

**5. Dans `uvicorn maintai.api.main:app` ?**  
`maintai.api.main` est le module `maintai/api/main.py` écrit avec des points ; `app` est la variable de ce module qui contient l'application FastAPI.

## 7. Point Git

- **Mon fichier :** `tp/tp1/compte_rendu_Wenn_BOUKA.md`, à côté de ceux de Yahya, Ahmed et Mazine
- **Branche :** `tp-wenn-bouka`, avec mes comptes rendus des TP1 à TP4
- **Intégration :** pull request de `tp-wenn-bouka` vers `main`
- **Exclus du dépôt :** `.venv`, `data/*.csv`, `models/`, `.env` (voir `.gitignore`)

## 8. Ce que je retiens

L'ordre des contrôles fait la robustesse de l'API : la route, puis le schéma, puis le modèle. Une valeur absurde est refusée avant de coûter une prédiction, et chaque échec a son code (404, 422, 503) qui dit au client *ce qu'il doit corriger*.

**Ce qui reste flou :** les bornes sont du bon sens physique, pas des spécifications constructeur. Sur de vraies machines, il faudrait les confirmer avec la fiche technique des capteurs (plage de mesure réelle du capteur de vibration notamment).
