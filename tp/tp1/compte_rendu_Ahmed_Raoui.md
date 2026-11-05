# Compte rendu · TP1 : transformer le modèle MaintAI en API

**Auteur :** Ahmed RAOUI  
**Email :** ahmedraoui1818@gmail.com  
**Groupe :** G1  
**Date :** 05/11/2026

---

## 1. Mise en place

L'objectif du TP est d'exposer le modèle de prédiction de panne de MaintAI sous forme d'API. Un client envoie un relevé de capteurs au format JSON ; l'API renvoie la probabilité de panne et une alerte lorsque cette probabilité atteint le seuil de 0,3.

Préparation du projet :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Au départ, avant toute modification du code, `pytest` indique :

```text
3 failed, 10 passed, 1 warning
```

Dans `tests/test_api.py`, 4 tests sur 7 réussissent déjà : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Deux de ces tests attendent un code 422 et passent pour une mauvaise raison. Le schéma d'entrée est vide et `extra="forbid"` rejette tout champ inconnu : toutes les requêtes reçoivent donc 422, y compris un relevé correct. Cela se vérifie avec `test_predict_returns_probability`, qui envoie un relevé valide et échoue avec `assert 422 == 200`. Conclusion : un test vert ne prouve rien tant qu'on ne sait pas pourquoi il est vert.

## 2. Schéma d'entrée (`maintai/api/schemas.py`)

Les bornes sont choisies selon des limites physiques : elles écartent ce qu'un capteur ou une machine ne peut pas mesurer. Elles ne reprennent pas le minimum et le maximum observés dans les données, car une machine en très mauvais état doit pouvoir être évaluée au lieu d'être refusée.

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification |
|---|---|---:|---:|---|
| `temperature_c` | `float` | -40 | 150 | Démarrage à froid dans un local non chauffé. Au-delà de 150 °C, un capteur défectueux est plus probable qu'un moteur réellement à cette température. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration n'est jamais négative ; 50 mm/s laisse une grande marge pour une machine très dégradée. |
| `load_pct` | `float` | 0 | 100 | Pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | `float` | 0 | 100 000 | Un compteur cumulé ne peut pas être négatif ; 100 000 h correspondent à environ 11 ans de fonctionnement continu. |

Avec `schemas.py` seul complété, il reste 3 échecs, mais l'erreur a changé :

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed
```

C'est une progression : le schéma accepte désormais les relevés valides, et la requête atteint la fonction `predict()`, qu'il reste à écrire.

## 3. L'API FastAPI (`maintai/api/main.py`)

Le corps de `predict()` récupère le modèle chargé au démarrage et renvoie sa prédiction :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

**503 plutôt que 500.** Un 500 correspond à une erreur inattendue, par exemple un bug. Ici, la cause est connue : le service n'est pas disponible tant que le modèle n'a pas été entraîné. Le 503 exprime exactement cela, et le message dit quoi faire.

**Modèle chargé une seule fois.** Relire le fichier du modèle à chaque requête ralentirait toutes les réponses. Chargé au démarrage, le modèle reste en mémoire dans `state` et sert toutes les requêtes. Son absence est de plus détectée dès le lancement et signalée par `/health`.

## 4. Les tests

À la fin du TP, tous les tests passent :

```text
13 passed, 1 warning
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | santé, prédiction, alerte, rejet 422, erreur 503, documentation |
| `tests/test_data.py` | 3 | les données |
| `tests/test_train.py` | 3 | l'entraînement du modèle |

Ces 13 tests correspondent au tag `tp1`. L'activité de la séance 5 ajoute `tests/test_casser.py` (5 cas), ce qui porte le total à 18 tests.

## 5. L'API en fonctionnement

Lancement du serveur :

```powershell
uvicorn maintai.api.main:app --reload
```

La documentation interactive est disponible sur `http://localhost:8000/docs`.

| Requête | Code | Réponse |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,...}` |
| `POST /v1/predict` avec une température de 500 | 422 | `Input should be less than or equal to 150` |
| `POST /v1/predicte` (faute de frappe) | 404 | `{"detail":"Not Found"}` |

Sans modèle entraîné, `/health` répond `{"status":"ok","model_loaded":false}` et `POST /v1/predict` répond 503.

Dans `/docs`, les bornes sont visibles dans le schéma `SensorReading` : chaque champ affiche son type, son minimum, son maximum et sa description.

## 6. Questions de compréhension

**1. REST et FastAPI : quelle différence ?**
REST est un ensemble de principes pour concevoir une API web (URL lisibles, méthodes HTTP, codes de statut, JSON). FastAPI est la bibliothèque Python qui permet d'écrire une API respectant ces principes.

**2. À quoi sert le schéma Pydantic ?**
- Il valide les requêtes : une valeur invalide donne 422.
- Il documente l'API, avec la page `/docs`.
- Il fournit à la fonction un objet Python typé et déjà vérifié.

**3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**
- `localhost` : l'ordinateur local.
- `8000` : le port sur lequel uvicorn écoute.
- `/v1/predict` : la route définie dans le code, et non un dossier sur le disque.

**4. Pourquoi `/v1` dans l'adresse ?**
C'est le numéro de version de l'API. Si le contrat change, on peut publier une `/v2` sans casser les clients qui utilisent encore la `/v1`.

**5. Dans `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**
- `maintai.api.main` : le fichier `maintai/api/main.py`, écrit avec des points.
- `app` : la variable de ce fichier qui contient l'application FastAPI.

## 7. Point Git

- **Dépôt commun du groupe :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp1`
- **Mon fichier :** `compte_rendu_Ahmed_Raoui.md`, à côté de celui de Yahya Baid (un compte rendu par membre)
- **Branche de travail :** `tp1-ahmed`
- **Pull request :** ouverte de `tp1-ahmed` vers `main`, visible dans l'onglet *Pull requests* du dépôt
- **Relecture :** faite par Yahya Baid avant la fusion
- **Tag `tp1` :** présent sur GitHub
- **Exclus du dépôt :** `.venv`, les données CSV et le dossier `models`

## 8. Conclusion

L'API refuse une valeur impossible avant même d'appeler le modèle, renvoie une probabilité et une alerte pour un relevé valide, et répond 503 avec une consigne claire quand le modèle est absent. Les 13 tests attendus passent. Les choix de bornes et le comportement sans modèle sont justifiés dans `docs/adr/002-validation.md`.

## 9. Ce qui reste flou

- **Créer n'est pas activer un environnement virtuel.** En début de séance, `python -m pytest` m'a répondu « No module named pytest ». J'avais bien créé `.venv` avec `python -m venv .venv`, mais sans l'activer : `python` utilisait donc le Python global, qui n'a pas pytest. Je dois encore prendre le réflexe de vérifier que `(.venv)` apparaît au début de la ligne du terminal avant de lancer quoi que ce soit.
- **Un test vert n'est pas forcément un test juste.** J'ai compris pourquoi deux tests 422 passaient avec un schéma vide (tout est refusé), mais je reste prudent : je ne sais pas encore repérer à coup sûr ce genre de faux positif sans faire échouer le test exprès pour voir s'il réagit.
