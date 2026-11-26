# TP1 — MaintAI : mettre le modèle derrière une API

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 22/10/2026 à 10:25  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `Livrables/Mazine_CHATER/TP1`

---

## 1. Prise en main

Le but du TP est de transformer le modèle de prédiction de panne en un service appelable par d'autres programmes. Un client envoie quatre mesures de capteurs au format JSON ; l'API renvoie une probabilité de panne et une alerte lorsque celle-ci atteint le seuil de 0,3.

Je commence par préparer l'environnement et par vérifier l'état du projet :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Le premier `pytest` donne :

```text
3 failed, 10 passed, 1 warning
```

Quatre des sept tests de l'API passent déjà. Deux d'entre eux attendent un code 422 et semblent donc corrects. En regardant de plus près, ils passent pour une mauvaise raison : le schéma `SensorReading` est encore vide et `extra="forbid"` fait refuser tous les champs. Même un relevé valide reçoit 422. Le test `test_predict_returns_probability` le prouve : il échoue avec `assert 422 == 200`.

J'en retiens qu'un test vert n'est pas une preuve en soi. Il faut aussi comprendre pourquoi il est vert.

## 2. Le schéma d'entrée

Les bornes sont définies dans `maintai/api/schemas.py` :

| Champ | Type | Minimum | Maximum | Justification |
|---|---|---:|---:|---|
| `temperature_c` | `float` | -40 | 150 | -40 °C couvre un démarrage à froid ; au-delà de 150 °C, un capteur défaillant est plus probable qu'un moteur réellement à cette température. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration ne peut pas être négative ; 50 mm/s laisse de la marge pour une machine très dégradée. |
| `load_pct` | `float` | 0 | 100 | Charge en pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | `float` | 0 | 100 000 | Compteur cumulé non négatif ; 100 000 h représentent environ onze ans de marche continue. |

Ces bornes ne recopient pas le minimum et le maximum du fichier CSV. Elles correspondent à ce qu'un capteur peut mesurer. Une machine en mauvais état doit rester analysable : si on rejetait toutes les valeurs rares, le modèle serait inutilisable au moment où on en a le plus besoin.

Après avoir complété `schemas.py`, les trois échecs restants changent de nature :

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed
```

La validation passe désormais et la requête arrive jusqu'à `predict()`, qui reste à écrire.

## 3. La route de prédiction

Le corps de la fonction dans `maintai/api/main.py` :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

**Pourquoi 503 et pas 500 ?** Le code 500 signale une erreur imprévue, comme un bug. Ici, la cause est connue : le service ne peut pas répondre tant que le modèle n'a pas été entraîné. Le 503 décrit cette indisponibilité temporaire et le message indique la marche à suivre.

**Pourquoi charger le modèle une seule fois ?** Le modèle est chargé dans `lifespan`, au démarrage de l'application, puis conservé dans `state`. Le relire à chaque requête serait inutilement lent. L'API démarre quand même si le fichier est absent : `/health` répond alors avec `model_loaded: false` et `/v1/predict` renvoie 503. Ce choix permet de diagnostiquer le problème sans faire planter le serveur.

## 4. Tests et vérifications

À la fin du TP, les 13 tests passent :

```text
13 passed, 1 warning
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | santé, prédiction, alerte, rejet 422, erreur 503, documentation |
| `tests/test_data.py` | 3 | chargement et découpage des données |
| `tests/test_train.py` | 3 | entraînement et artefacts du modèle |

En séance 5, `tests/test_casser.py` ajoute cinq cas et `tests/test_demo.py` un test, ce qui porte le total à 19 tests.

Quelques requêtes envoyées au serveur :

| Requête | Code | Réponse |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec un relevé normal | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,...}` |
| `POST /v1/predict` avec `temperature_c = 500` | 422 | `Input should be less than or equal to 150` |
| `POST /v1/predicte` | 404 | `{"detail":"Not Found"}` |

Sans modèle entraîné, `/health` renvoie `{"status":"ok","model_loaded":false}` et la prédiction répond 503.

La page `/docs` affiche le schéma `SensorReading` avec le type, les bornes et la description de chaque champ. C'est la même définition Pydantic qui sert à valider et à documenter.

## 5. Réponses aux questions

**1. REST et FastAPI, quelle différence ?**  
REST est une façon de concevoir une API web : des URL claires, les méthodes HTTP, des codes de statut et du JSON. FastAPI est la bibliothèque Python qui permet d'écrire une API selon ces principes.

**2. À quoi sert le schéma Pydantic ?**  
Il a trois rôles : valider les données reçues, documenter l'API dans `/docs`, et fournir à la fonction un objet Python typé déjà vérifié.

**3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**  
`localhost` est la machine locale, `8000` le port d'écoute d'uvicorn, et `/v1/predict` la route définie dans le code, pas un dossier du disque.

**4. Pourquoi `/v1` dans l'adresse ?**  
C'est la version de l'API. Si le contrat change, une `/v2` peut être publiée sans casser les clients qui utilisent encore `/v1`.

**5. Dans `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**  
`maintai.api.main` est le chemin du module `maintai/api/main.py`, écrit avec des points. `app` est la variable de ce module qui contient l'application FastAPI.

## 6. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `Livrables/Mazine_CHATER/TP1`
- **Mon fichier :** `CR_TP1_Mazine_CHATER.md`, déposé à côté des comptes rendus de mes camarades
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp1`
- **Fichiers exclus :** `.venv`, les CSV générés, le dossier `models` et les caches

## 7. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| Bornes physiques plutôt que min/max des données | Un capteur peut mesurer -40 °C ou 150 °C, même si le fichier d'entraînement ne contient jamais ces extrêmes. Copier les min/max du CSV reviendrait à refuser une machine qui se dégrade au pire moment. Les bornes écartent une mesure impossible, pas une mesure rare. |
| Tous les champs en `float` | Les capteurs renvoient des mesures continues, comme 72,5 °C ou 6,1 mm/s. Un entier refuserait ou tronquerait ces valeurs ; le pourcentage de charge peut aussi être décimal. |
| `POST /v1/predict` plutôt que `GET` | Le relevé complet voyage dans le corps JSON au lieu d'être découpé en paramètres d'URL. Cela évite de retrouver les mesures dans les journaux et correspond à une opération qui produit un résultat. |
| Réponse en JSON | C'est un format lisible par n'importe quel client et FastAPI le documente automatiquement dans `/docs`. |
| `extra="forbid"` dans le schéma | Un champ inconnu est souvent une faute de frappe ou un client qui n'utilise pas le bon contrat. Le refuser en 422 rend le problème visible ; l'ignorer silencieusement produirait une prédiction sur des données incomplètes. |
| Schéma séparé de la route (`schemas.py`) | Le contrat d'entrée est plus facile à relire, à tester et à documenter quand il n'est pas mélangé avec le code de la route. `main.py` reste centré sur le traitement de la requête. |
| `model_dump()` avant la prédiction | Le prédicteur attend un dictionnaire. `model_dump()` fait la conversion sans exposer les attributs Pydantic au reste du code. |
| 503 plutôt que 500 quand le modèle manque | Le 500 est réservé aux erreurs imprévues. Ici, l'absence de modèle est un état connu et temporaire : le 503 indique au client de réessayer après entraînement, et le message donne la commande à lancer. |
| Chargement du modèle une seule fois dans `lifespan` | Relire un fichier joblib à chaque requête ajouterait une attente inutile. Le chargement au démarrage garantit aussi que le modèle est prêt avant la première prédiction. |
| L'API démarre même sans modèle | Un serveur qui refuse de démarrer ne permet même pas de consulter `/health`. En démarrant quand même, on voit `model_loaded: false` et on peut corriger sans boucle de crash. |
| `/health` non protégé | Une supervision doit pouvoir vérifier le service sans posséder la clé. La route n'expose que l'état et la présence du modèle, pas de données sensibles. |
| Seuil d'alerte à 0,3 | C'est un choix métier, pas une vérité mathématique. Un seuil bas privilégie la détection : on accepte quelques fausses alertes plutôt que de manquer une panne. Le seuil reste réglable par variable d'environnement. |
| Préfixe `/v1` | Il permet de faire évoluer le contrat sans casser les clients existants. Une future `/v2` pourrait cohabiter avec `/v1`. |
| Tests sur les bornes, l'alerte et le 503 | Les tests ne couvrent pas seulement le cas nominal. Ils vérifient les frontières du schéma, l'absence de modèle et le déclenchement de l'alerte, qui sont les comportements les plus faciles à casser. |

## 8. Ce que je retiens

Le point le plus important du TP est l'ordre des contrôles : la validation du schéma se fait avant l'appel au modèle. Une requête aberrante ne coûte donc même pas une prédiction.

Il me reste une zone d'ombre sur le comportement de l'API quand plusieurs dépendances sont branchées sur une route : je sais que la clé est vérifiée avant le corps de la fonction, mais je veux encore vérifier l'ordre exact lorsque plusieurs `Depends` sont en jeu. Je n'ai pas non plus testé le modèle sur de vraies données de maintenance ; les bornes actuelles sont des choix de bon sens, à confirmer avec des mesures réelles.
