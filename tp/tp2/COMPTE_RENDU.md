# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1My ·  **Membres :** Yahya Baid ·  **Date :** 05/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

Base : `VALID = {"temperature_c": 60.0, "vibration_mm_s": 2.0, "load_pct": 50.0, "runtime_hours": 5000}`. Les requêtes ont été envoyées à un serveur uvicorn lancé, par un script et non depuis `/docs`.

| Requête | Ce qui ne va pas | Corps ou URL | Code prévu | Code obtenu |
|---|---|---|---|---|
| 1 | champ manquant | `POST /v1/predict`, `VALID` sans `load_pct` | 422 | 422 |
| 2 | valeur absurde | `POST /v1/predict`, `load_pct: 250` | 422 | 422 |
| 3 | texte au lieu d'un nombre | `POST /v1/predict`, `temperature_c: "chaud"` | 422 | 422 |
| 4 | champ en trop | `POST /v1/predict`, `couleur: "rouge"` | 422 | 422 |
| 5 | mauvaise route | `POST /v1/predire`, `VALID` | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq codes obtenus sont ceux prévus. Le champ en trop est refusé parce que `SensorReading` déclare `extra="forbid"` : sans ce réglage, Pydantic l'ignorerait et l'API répondrait 200. Aucune borne de `schemas.py` n'a eu besoin d'être corrigée.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
18 passed, 1 warning in 5.20s
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

Il lance une même fonction de test une fois par ligne d'une liste de cas, sans recopier le code, et nomme chaque cas dans le rapport. pytest compte 5 tests pour `test_requete_refusee`, car la liste `CAS_REFUSES` contient 5 lignes : chaque ligne réussit ou échoue indépendamment des autres.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
All checks passed!
```

Sortie obtenue après `ruff check . --fix`, qui a corrigé l'alias `UP017` signalé dans `train.py` sans casser de test. Dans `TP/TP2`, le même contrôle signalait au départ 8 erreurs : 6 F401 (les imports préparés mais pas encore utilisés), 1 I001 et 1 UP017. Une fois le code du sprint 1 écrit, `--fix` a corrigé les deux dernières sans casser de test.

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff` lit le code sans l'exécuter et vérifie sa qualité d'écriture : imports inutiles ou mal rangés, variables jamais utilisées. `pytest` exécute le code et vérifie son comportement : pour telle requête, le code de réponse attendu. Un code peut être propre pour ruff et faux pour pytest, ou l'inverse.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed, 16 passed, 1 warning in 7.12s
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

`test_missing_key_is_rejected` (sans clé) et `test_wrong_key_is_rejected` (fausse clé), dans `tests/test_security.py`. Ils reçoivent **200** au lieu de 401, car l'API ne vérifie pas encore la clé.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée",
        )
    # encode() : compare_digest refuse les str contenant des caractères non ASCII
    if x_api_key is None or not secrets.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours 2 (`2 failed, 16 passed`). La fonction existe, mais aucune route ne l'appelle : les requêtes sans clé reçoivent encore 200.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
18 passed in 5.39s
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

Le relevé normal est `VALID` (section 1). Les requêtes ont été envoyées par un script au serveur lancé avec `--env-file .env` (sans `--reload`). La version du modèle change à chaque entraînement.

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"2026-11-05T09:41:50Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Les contrôles s'enchaînent et le premier qui échoue donne la réponse : la route, la clé, les données, puis le modèle. Sans clé, la requête s'arrête au contrôle de la clé (401) et les données ne sont pas regardées. Avec la clé, elle atteint la validation du schéma, qui refuse 500 °C (422).

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

**500** : `{"detail":"La clé API du serveur n'est pas configurée"}`. La faute vient du serveur, qui n'a aucune clé à comparer, et non du client, dont la clé n'est pas forcément fausse. Un 401 l'enverrait chercher une erreur qu'il n'a pas commise.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
const adresse = document.getElementById("url").value.replace(/\/+$/, "") + "/v1/predict";
const cle = document.getElementById("key").value;
try {
  const resp = await fetch(adresse, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": cle },
    body: JSON.stringify(reading),
  });
  const data = await resp.json();
  if (!resp.ok) {
    // 401 et 503 : detail est un texte ; 422 : une liste d'erreurs de validation
    const detail = Array.isArray(data.detail)
      ? data.detail.map(d => `${d.loc.at(-1)} : ${d.msg}`).join(" ; ")
      : data.detail;
    show("err", `Erreur ${resp.status} : ${detail}`);
    return;
  }
  const pct = (data.failure_probability * 100).toFixed(1);
  if (data.alert) {
    show("alert", `ALERTE : probabilité de panne ${pct} %`);
  } else {
    show("ok", `Pas d'alerte : probabilité de panne ${pct} %`);
  }
} catch (e) {
  show("err", `API injoignable (arrêtée, ou origine refusée par CORS) : ${e.message}`);
}
```

Ce qu'affiche la page (servie sur le port 5500) :

Essais réalisés dans Chrome, page pilotée par un script (Playwright).

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | `Pas d'alerte : probabilité de panne 0.3 %` |
| 500 °C, bonne clé | `Erreur 422 : temperature_c : Input should be less than or equal to 150` |
| relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide` |

Avec les valeurs par défaut de la page (72 °C, 6 mm/s, 85 %, 15 000 h) et la bonne clé, elle affiche `ALERTE : probabilité de panne 94.8 %`.

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche : `API injoignable (arrêtée, ou origine refusée par CORS) : Failed to fetch`.

La console affiche :

```
Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle appliquée par le navigateur, pas par l'API. Le navigateur demande la permission (`OPTIONS`) ; l'API répond 400 `Disallowed CORS origin` et il ne lance donc pas le POST. `curl.exe` n'est pas un navigateur : il envoie directement le POST et reçoit 200 avec la bonne clé, même en annonçant `Origin: http://localhost:5501`. CORS protège l'utilisateur d'une page malveillante, tandis que l'API, elle, est protégée par la clé.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

**4 tests échouent** (`4 failed, 1 passed`) : ils reçoivent **401** au lieu de 422 (`assert 401 == 422`), car la clé est vérifiée avant les données. La **mauvaise route** passe quand même : `/v1/predire` n'existe pas, la requête s'arrête au contrôle de la route avec 404, avant celui de la clé.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
23 passed, 1 warning in 5.33s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   401 : l'appelant n'est pas authentifié (clé absente ou fausse). 422 : l'appelant est accepté, mais ses données sont refusées par le schéma. 403 : l'appelant est bien identifié, mais il n'a pas le droit de faire cette action (autorisation, hors TP2).
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Une clé commitée finit sur GitHub et reste dans l'historique même si on supprime le fichier ensuite ; il faut alors la changer. `.env` contient la vraie clé et les origines, reste sur le poste et est exclu par `.gitignore`. `.env.example` contient les mêmes variables avec une fausse valeur et dit quoi configurer : c'est lui qui est commité.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout, notamment dans les journaux du serveur et l'historique du navigateur : la clé y serait exposée.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   Sa durée ne dépend pas de la position du premier caractère différent. `==` s'arrête au premier caractère faux, et un attaquant pourrait mesurer le temps de réponse pour deviner la clé caractère par caractère.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est le trio schéma, domaine et port. Ces deux adresses ne sont pas la même origine, car leur port diffère. L'appel de la page vers l'API est donc soumis à CORS.

## 8. Le rendu Git

- Lien de la pull request : aucune pull request ; la branche `tp2` a été fusionnée directement dans `main` (commit de fusion).
- Le tag `tp2` existe sur GitHub : oui
- `git status` avant le commit : le fichier `.env` apparaissait-il ? non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Aucune relecture : il n'y a pas eu de pull request.

## 9. Ce qui reste flou

…
