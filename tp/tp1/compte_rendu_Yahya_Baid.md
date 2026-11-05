# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Auteur :** Yahya Baid  
**Email :** yahya04ba@gmail.com  
**Groupe :** G1My  
**Date :** 05/11/2026

---

## 1. Mise en place

Le TP transforme le modèle de prédiction de panne de MaintAI en API : un programme envoie un relevé de capteurs en JSON et reçoit la probabilité de panne, avec une alerte si elle atteint le seuil de 0,3. Le projet se prépare avec ces commandes :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Juste après la mise en place, avant d'écrire le moindre code, `pytest` donne :

```text
3 failed, 10 passed, 1 warning in 5.67s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà :

- `test_health`
- `test_out_of_range_value_is_rejected`
- `test_missing_field_is_rejected`
- `test_openapi_documents_predict`

Les deux tests qui attendent un code 422 passent pour une mauvaise raison. Le schéma est encore vide et `extra="forbid"` refuse tout champ inconnu : tous les relevés reçoivent donc 422, même un relevé correct. La preuve : `test_predict_returns_probability`, qui envoie un bon relevé, échoue à ce stade avec `assert 422 == 200`. Un test vert ne suffit donc pas, il faut aussi comprendre pourquoi il passe.

## 2. Schéma d'entrée (`maintai/api/schemas.py`)

Les bornes sont physiques : elles refusent ce qu'une machine ou un capteur ne peut pas afficher, et ne sont pas copiées sur le minimum et le maximum des données. Une machine anormale doit pouvoir être évaluée, et non rejetée.

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification |
|---|---|---:|---:|---|
| `temperature_c` | `float` | -40 | 150 | Démarrage à froid dans un local non chauffé ; au-delà de 150 °C, on soupçonne un capteur défaillant plutôt qu'une mesure normale de moteur. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration mesurée n'est pas négative ; 50 mm/s laisse une large marge pour une machine très dégradée. |
| `load_pct` | `float` | 0 | 100 | Pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | `float` | 0 | 100 000 | Un compteur cumulé n'est pas négatif ; 100 000 h représentent environ 11 ans de marche continue. |

Après avoir écrit `schemas.py` seul, `pytest` donne encore 3 échecs, mais avec une autre erreur :

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed in 7.34s
```

C'est bon signe : le schéma accepte maintenant les relevés valides et la requête arrive jusqu'à `predict()`. Il ne reste qu'à écrire cette fonction.

## 3. API FastAPI et logique métier (`maintai/api/main.py`)

Le corps de la fonction `predict()` récupère le modèle chargé au démarrage, puis renvoie sa prédiction :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

### Pourquoi 503 et pas 500 ?

Le code 500 signale une erreur imprévue, comme un bug dans le code. Ici, la situation est connue : le service reste indisponible tant que le modèle n'est pas entraîné. Le code 503 le dit précisément, et le message indique quoi faire.

### Pourquoi charger le modèle une seule fois ?

Lire le fichier du modèle sur le disque à chaque requête ralentirait toutes les réponses. Chargé une seule fois au démarrage, il reste en mémoire dans `state` et sert à toutes les requêtes. Son absence est aussi détectée dès le lancement et signalée par `/health`.

## 4. Les tests

À la fin du TP, les 13 tests passent :

```text
13 passed, 1 warning in 5.67s
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | l'API : santé, prédiction, alerte, 422, 503, documentation |
| `tests/test_data.py` | 3 | les données |
| `tests/test_train.py` | 3 | l'entraînement du modèle |

Ces 13 tests correspondent au tag `tp1`. La séance 5 ajoute ensuite `tests/test_casser.py` et ses 5 cas, puis `tests/test_demo.py` et son test `test_500_degres_est_refuse`, l'exemple du polycopié. Sur `main`, ce dossier compte donc 19 tests, tous réussis :

```text
19 passed, 1 warning in 4.77s
```

## 5. L'API en marche

Le serveur se lance avec :

```powershell
uvicorn maintai.api.main:app --reload
```

La documentation interactive est alors disponible sur `http://localhost:8000/docs`.

Les requêtes ci-dessous ont été envoyées par un script à un serveur uvicorn lancé sur le port 8001, sans `--reload`, car le port 8000 était déjà occupé. La version du modèle change à chaque entraînement.

| Requête | Code obtenu | Réponse |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-05T10:04:16Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe) | 404 | `{"detail":"Not Found"}` |

Avec un dossier de modèles vide, `/health` répond `{"status":"ok","model_loaded":false}` et `POST /v1/predict` répond 503.

Dans `/docs`, les bornes apparaissent dans la description du schéma `SensorReading` : l'onglet **Schema** du corps de la requête `POST /v1/predict`, et la section **Schemas** en bas de la page. Chaque champ y affiche son type, son minimum, son maximum et sa description.

## 6. Réponses aux questions de compréhension

**1. REST et FastAPI : quelle est la différence ?**

- REST est un ensemble de règles pour concevoir une API web : URL claires, méthodes HTTP, codes précis, JSON.
- FastAPI est la bibliothèque Python avec laquelle on écrit une API qui suit ces règles.

**2. Le schéma Pydantic sert à trois choses. Lesquelles ?**

- Valider les requêtes : une valeur invalide donne 422.
- Documenter l'API : la page `/docs`.
- Donner à la fonction un objet Python typé, déjà vérifié.

**3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**

- `localhost` : la machine elle-même.
- `8000` : le port où uvicorn écoute.
- `/v1/predict` : la route, un chemin défini dans le code et non un dossier sur le disque.

**4. Pourquoi `/v1` dans l'adresse ?**

C'est la version de l'API. Si le contrat change, on peut publier `/v2` sans casser les clients qui utilisent encore `/v1`.

**5. Dans `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**

- `maintai.api.main` : le fichier `maintai/api/main.py`, écrit avec des points.
- `app` : la variable de ce fichier qui contient l'application FastAPI.

## 7. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp1`
- **Branche de travail :** `tp1`, fusionnée dans `main` par un commit de fusion
- **Pull request :** aucune, la fusion a été faite directement
- **Relecture :** aucune, puisqu'il n'y a pas eu de pull request
- **Tag `tp1` :** présent sur GitHub
- **Fichiers exclus du dépôt :** `.venv`, les données CSV et le dossier `models`

## 8. Conclusion

L'API refuse une valeur impossible avant d'appeler le modèle, renvoie une probabilité et une alerte pour un relevé valide, et répond 503 avec une consigne claire si le modèle manque. Les 13 tests attendus passent. Les choix de bornes et le comportement sans modèle sont justifiés dans `docs/adr/002-validation.md`.

## 9. Ce qui reste flou

…
