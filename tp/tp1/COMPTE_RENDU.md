# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1My  ·  **Membres :** Yahya Baid  ·  **Date :** 05/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning in 5.67s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests sont `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests qui attendent 422 sont `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`. Ils passent pour une mauvaise raison : le schéma est vide et `extra="forbid"` refuse tout champ inconnu. Tous les relevés reçoivent donc 422, même un relevé correct, et non parce que la valeur est hors bornes ou qu'un champ manque. La preuve : `test_predict_returns_probability`, qui envoie un bon relevé, échoue à ce stade avec `assert 422 == 200`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | Démarrage à froid dans un local non chauffé ; au-delà de 150 °C, on soupçonne un capteur défaillant plutôt qu'une mesure normale de moteur. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration mesurée n'est pas négative ; 50 mm/s laisse une large marge pour une machine très dégradée. |
| `load_pct` | `float` | 0 | 100 | Pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | `float` | 0 | 100 000 | Un compteur cumulé n'est pas négatif ; 100 000 h représentent environ 11 ans de marche continue. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed in 7.34s
```

Le nombre d'échecs ne change pas, mais l'erreur n'est plus la même : on est passé de 422 à `NotImplementedError`. C'est bon signe, car le schéma accepte maintenant les relevés valides et la requête arrive jusqu'à `predict()`. Il ne reste qu'à écrire cette fonction.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 signale une erreur imprévue, comme un bug dans le code. Ici, la situation est connue : le service est indisponible tant que le modèle n'est pas entraîné. 503 le dit précisément, et le message indique quoi faire.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Lire le fichier du modèle sur le disque à chaque requête ralentirait toutes les réponses. Chargé une seule fois, il reste en mémoire dans `state` et sert à toutes les requêtes. Son absence est aussi détectée dès le démarrage et signalée par `/health`.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 5.67s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

Les requêtes ont été envoyées par un script à un serveur uvicorn lancé sur le port 8001 (sans `--reload`), le port 8000 étant déjà occupé. La version du modèle change à chaque entraînement.

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-05T10:04:16Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Avec un dossier de modèles vide, `/health` répond `{"status":"ok","model_loaded":false}` et `POST /v1/predict` répond 503.

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la description du schéma `SensorReading` : l'onglet **Schema** du corps de la requête de `POST /v1/predict`, et la section **Schemas** en bas de la page. Chaque champ y affiche son type, son minimum, son maximum et sa description.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de règles pour concevoir une API web : URL claires, méthodes HTTP, codes précis, JSON. FastAPI est la bibliothèque Python avec laquelle on écrit une API qui suit ces règles.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Valider les requêtes (422 si une valeur est invalide), documenter l'API (la page `/docs`) et donner à la fonction un objet Python typé, déjà vérifié.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est la machine elle-même, `8000` le port où uvicorn écoute, et `/v1/predict` la route, un chemin défini dans le code et non un dossier sur le disque.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version de l'API. Si le contrat change, on peut publier `/v2` sans casser les clients qui utilisent encore `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le fichier `maintai/api/main.py` écrit avec des points, et `app` est la variable de ce fichier qui contient l'application FastAPI.

## 7. Le rendu Git

- Lien de la pull request : aucune pull request ; la branche `tp1` a été fusionnée directement dans `main` (commit de fusion).
- Le tag `tp1` existe sur GitHub : oui
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Aucune relecture : il n'y a pas eu de pull request.

## 8. Ce qui reste flou

…
