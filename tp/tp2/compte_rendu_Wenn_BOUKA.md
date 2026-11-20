# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Auteur :** Wenn BOUKA  
**Groupe :** G1  
**Date :** 20/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp2`

---

## 1. Activité 1 : casser son API (dans `tp/tp1`)

Avant d'envoyer chaque requête, j'ai noté le code attendu.

| # | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---:|---:|
| 1 | champ manquant (`load_pct` absent) | 422 | 422 |
| 2 | valeur absurde (`load_pct = 250`) | 422 | 422 |
| 3 | texte au lieu d'un nombre (`temperature_c = "chaud"`) | 422 | 422 |
| 4 | champ en trop (`couleur = "rouge"`) | 422 | 422 |
| 5 | mauvaise route (`POST /v1/predire`) | 404 | 404 |

**Une prévision fausse ?** Non. Le cas 4 est le seul où j'ai hésité : par défaut Pydantic *ignore* un champ inconnu et l'API aurait répondu 200. C'est `extra="forbid"` dans `SensorReading` qui le transforme en 422. Le cas 3 est refusé parce que `"chaud"` ne se convertit pas en `float` (alors que `"72"` passerait).

**`python -m pytest` dans `tp/tp1` avec `tests/test_casser.py` :**

```text
19 passed, 1 warning
```

(13 tests du TP1 + 5 cas de `test_casser.py` + `test_500_degres_est_refuse` de `test_demo.py`.)

**À quoi sert `@pytest.mark.parametrize` ?** Il exécute la même fonction de test une fois par ligne d'une liste de cas. pytest compte donc **5 tests** pour `test_requete_refusee`, un par ligne de `CAS_REFUSES`, chacun avec son propre identifiant dans le rapport (`[champ manquant-...]`, etc.) : un cas qui casse n'empêche pas les autres de s'exécuter.

## 2. ruff

```text
$ ruff check .
All checks passed!
```

(dans `tp/tp1` comme dans `tp/tp2`, une fois le code écrit.)

**`ruff check .` contre `python -m pytest` :** ruff **lit** le code sans l'exécuter et contrôle sa forme (imports inutiles ou mal triés, variables jamais lues, tournures obsolètes). pytest **exécute** le code et contrôle son comportement (telle requête → tel code). Un code peut être impeccable pour ruff et faux pour pytest, ou l'inverse ; il faut les deux.

## 3. Mise en place du TP2 (dans `tp/tp2`)

Juste après la mise en place :

```text
FAILED tests/test_security.py::test_missing_key_is_rejected - AssertionError: assert 200 == 401
FAILED tests/test_security.py::test_wrong_key_is_rejected - assert 200 == 401
2 failed, 16 passed, 1 warning
```

Les deux tests reçoivent **200** au lieu de 401 : l'API répond encore à tout le monde, avec ou sans clé.

## 4. Sprint 1 : la clé API

### `maintai/api/security.py`

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

### Routeur dans `maintai/api/main.py`

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

**Avec `security.py` seul, sans toucher au routeur :** toujours `2 failed, 16 passed`. Écrire la fonction ne suffit pas, personne ne l'appelle. Elle ne protège les routes qu'une fois déclarée comme dépendance du routeur, et toutes les routes `/v1/...` sont alors protégées d'un coup (`/health`, hors routeur, reste libre).

**Fin du sprint 1 :**

```text
18 passed, 1 warning
```

### Requêtes HTTP

Serveur lancé avec `uvicorn maintai.api.main:app --env-file .env`, ma clé dans `.env` (jamais commitée). Relevé normal : `{"temperature_c": 60.0, "vibration_mm_s": 2.0, "load_pct": 50.0, "runtime_hours": 5000}`.

| Requête | Code | Réponse |
|---|---:|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,...}` |
| `temperature_c = 500`, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `temperature_c = 500`, bonne clé | 422 | `less_than_equal` · `Input should be less than or equal to 150` |

**Pourquoi 500 °C donne 401 sans clé et 422 avec ?** Les contrôles s'enchaînent dans un ordre fixe : route → clé → schéma → modèle, et le premier qui échoue répond. Sans clé, la requête s'arrête à la clé : le corps n'est même pas lu. Avec la clé, elle atteint le schéma, qui refuse 500 °C. Conséquence pratique : un inconnu ne peut pas sonder les bornes du schéma.

**Sans `--env-file .env`, avec ma clé :**

```text
500  {"detail":"La clé API du serveur n'est pas configurée"}
```

Ce n'est pas un 401, car le client n'a rien fait de mal : c'est le serveur qui n'a aucune clé à laquelle comparer. Un 401 enverrait le client chercher une erreur qui n'est pas la sienne.

## 5. Sprint 2 : la page web

### `fetch` dans `web/index.html`

```javascript
const resp = await fetch(adresse, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-API-Key": cle },
  body: JSON.stringify(reading),
});
const data = await resp.json();
if (!resp.ok) {
  // 401 / 503 : detail est un texte ; 422 : une liste d'erreurs de validation
  const detail = Array.isArray(data.detail)
    ? data.detail.map(d => `${d.loc.at(-1)} : ${d.msg}`).join(" ; ")
    : data.detail;
  show("err", `Erreur ${resp.status} : ${detail}`);
  return;
}
```

### Essais (page servie par `python -m http.server 5500 -d web`, ouverte dans Chrome)

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | `Pas d'alerte : probabilité de panne 0.3 %` |
| 500 °C, bonne clé | `Erreur 422 : temperature_c : Input should be less than or equal to 150` |
| relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide` |
| valeurs par défaut (72 °C, 6 mm/s, 85 %, 15 000 h), bonne clé | `ALERTE : probabilité de panne 94.8 %` |

### Expérience CORS (page servie sur le port 5501)

La page affiche :

```text
API injoignable (arrêtée, ou origine refusée par CORS) : Failed to fetch
```

La console (F12) :

```text
Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been
blocked by CORS policy: Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

J'ai rejoué les deux étapes à la main avec curl :

| Requête | Résultat |
|---|---|
| `OPTIONS` (pré-vérification), `Origin: http://localhost:5500` | 200, `access-control-allow-origin: http://localhost:5500` |
| `OPTIONS`, `Origin: http://localhost:5501` | 400, `Disallowed CORS origin` |
| `POST` direct, `Origin: http://localhost:5501`, bonne clé | **200**, prédiction renvoyée |

**Pourquoi curl passe et pas la page ?** CORS est appliqué **par le navigateur** : avant le POST, il demande la permission (`OPTIONS`) et, sans `Access-Control-Allow-Origin` pour son origine, il n'envoie pas la requête. curl n'est pas un navigateur et ignore ce mécanisme. CORS protège donc l'utilisateur contre une page tierce qui utiliserait son navigateur ; il ne protège pas l'API. Ce qui protège l'API, c'est la clé.

## 6. Les tests de l'activité 1 dans le TP2

**`test_casser.py` copié sans `headers=HEADERS` :**

```text
4 failed, 1 passed
```

Les quatre cas « données » reçoivent **401** au lieu de 422 : la clé est contrôlée avant le schéma. Le cas **mauvaise route** passe quand même : `/v1/predire` n'existe pas, la requête s'arrête au routage (404) avant même la vérification de clé.

**Avec `headers=HEADERS` :**

```text
tests/test_api.py .......          [ 30%]
tests/test_casser.py .....         [ 52%]
tests/test_data.py ...             [ 65%]
tests/test_security.py .....       [ 86%]
tests/test_train.py ...            [100%]

23 passed, 1 warning
```

## 7. Questions de compréhension

**1. 401 / 422 / 403 ?**  
401 : je ne sais pas qui vous êtes (clé absente ou fausse). 422 : je sais qui vous êtes, mais vos données sont invalides. 403 : je sais qui vous êtes, mais vous n'avez pas le droit de faire cela (autorisation, non utilisé ici).

**2. Pourquoi la clé n'est ni dans le code ni dans Git ?**  
Un secret commité reste dans l'historique même après suppression du fichier : il faut alors le révoquer. `.env` contient la vraie clé, reste sur le poste et est listé dans `.gitignore`. `.env.example` contient les mêmes variables avec des valeurs factices et documente la configuration : c'est lui qui est commité.

**3. Pourquoi un en-tête plutôt que l'URL ?**  
Une URL est recopiée partout : journaux du serveur et des proxys, historique du navigateur, en-tête `Referer`. Une clé dans l'URL fuit par tous ces chemins.

**4. `secrets.compare_digest` contre `==` ?**  
`==` s'arrête au premier caractère différent, donc le temps de réponse révèle combien de caractères sont justes, ce qui permet de deviner la clé caractère par caractère. `compare_digest` met le même temps quelle que soit la position de la différence.

**5. Qu'est-ce qu'une origine ?**  
Le triplet schéma + domaine + port. `http://localhost:5500` et `http://localhost:8000` diffèrent par le port : ce sont deux origines, et l'appel de l'une vers l'autre est soumis à CORS.

## 8. Point Git

- **Mon fichier :** `tp/tp2/compte_rendu_Wenn_BOUKA.md`
- **Branche :** `tp-wenn-bouka`, pull request vers `main`
- **`.env` dans `git status` avant le commit :** non, il est exclu par `.gitignore`
- **Exclus :** `.env`, `.venv`, `data/*.csv`, `models/`

## 9. Ce qui reste flou

- Une seule clé partagée par tous les clients : impossible de savoir qui a appelé, ou de révoquer un seul client. Je vois l'intérêt de clés par client (ou de jetons), mais pas encore comment les stocker et les faire tourner proprement.
- La page web garde la clé dans un champ du navigateur : pour une démo c'est acceptable, pour une vraie application publique la clé serait visible par l'utilisateur.
