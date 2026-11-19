# TP2 — MaintAI : tester, protéger et appeler l'API

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 05/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp2`

---

## 1. Activité 1 : casser l'API

Le but est d'envoyer de mauvaises requêtes à l'API du TP1 et de comparer le code prévu au code obtenu. Les requêtes ont été envoyées par un petit script à un serveur uvicorn déjà lancé.

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---:|---:|
| 1 | `load_pct` manquant | 422 | 422 |
| 2 | `load_pct = 250` | 422 | 422 |
| 3 | `temperature_c = "chaud"` | 422 | 422 |
| 4 | champ `couleur` ajouté | 422 | 422 |
| 5 | `POST /v1/predire` | 404 | 404 |

Mes cinq prévisions étaient justes. Le 422 sur le champ en trop vient de `extra="forbid"` dans `SensorReading` : sans cette option, Pydantic se contenterait d'ignorer `couleur` et l'API répondrait 200.

`@pytest.mark.parametrize` sert à exécuter une même fonction de test avec plusieurs jeux de valeurs. La liste `CAS_REFUSES` contient cinq lignes : pytest compte donc cinq tests distincts pour `test_requete_refusee`, et chaque cas peut réussir ou échouer séparément.

Avec `tests/test_casser.py`, le total du TP1 passe à 19 tests :

```text
19 passed, 1 warning
```

## 2. Analyse statique avec Ruff

```powershell
python -m ruff check .
```

```text
All checks passed!
```

Ruff lit le code sans l'exécuter. Il repère les imports inutilisés, les imports mal rangés, les variables jamais utilisées ou certaines pratiques déconseillées. Pytest fait un autre travail : il exécute le programme et vérifie son comportement.

Les deux outils sont complémentaires. Un code peut être parfait pour Ruff et produire une mauvaise réponse, ou réussir tous les tests tout en étant mal écrit. Dans le starter du TP2, Ruff signalait quelques imports préparés pour la suite ; une fois le code des sprints écrit, le contrôle est devenu propre.

## 3. Mise en place du TP2

Après installation des dépendances, le premier `pytest` dans `tp/tp2` donne :

```text
2 failed, 16 passed, 1 warning
```

Les deux échecs concernent l'authentification :

- `test_missing_key_is_rejected` : la requête sans clé reçoit 200 au lieu de 401.
- `test_wrong_key_is_rejected` : la requête avec une fausse clé reçoit 200 au lieu de 401.

À ce stade, l'API répond à tout le monde : la clé n'est pas encore contrôlée.

## 4. Protection par clé API (sprint 1)

La fonction ajoutée dans `maintai/api/security.py` :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().api_key
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée",
        )
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Et dans `maintai/api/main.py`, la dépendance est branchée sur le routeur :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

**401 ou 500 ?** Si la clé manque ou ne correspond pas, le problème vient du client : 401. Si le serveur n'a lui-même aucune clé configurée, il ne peut pas faire la comparaison : c'est une erreur du serveur, donc 500. Un 401 ferait croire à tort que le client s'est trompé.

**Pourquoi les tests échouent encore avec `security.py` seul ?** Parce qu'une fonction qui n'est appelée par aucune route ne protège rien. Il faut ajouter `Depends(require_api_key)` au routeur pour qu'elle s'exécute avant chaque requête.

Scénarios vérifiés :

| Scénario | Code | Explication |
|---|---:|---|
| `GET /health` sans clé | 200 | La route de santé n'est pas protégée. |
| `POST /v1/predict` sans clé | 401 | Authentification absente. |
| `POST /v1/predict` avec une fausse clé | 401 | Authentification invalide. |
| `POST /v1/predict` avec la bonne clé et un relevé valide | 200 | Requête acceptée. |
| `POST /v1/predict` à 500 °C sans clé | 401 | La clé est contrôlée avant les données. |
| `POST /v1/predict` à 500 °C avec la bonne clé | 422 | La validation refuse la température. |

Les contrôles s'enchaînent dans cet ordre : route, clé, données, modèle. Le premier qui échoue décide du code de réponse. C'est pour cela qu'une température de 500 °C ne donne pas le même résultat selon que la clé est présente ou non.

Si uvicorn est lancé sans `--env-file .env`, la variable `MAINTAI_API_KEY` est absente côté serveur et la réponse devient 500, avec le message « La clé API du serveur n'est pas configurée ».

## 5. Appel depuis la page web (sprint 2)

La page `web/index.html` reprend les quatre champs et envoie une requête `fetch` :

```javascript
const resp = await fetch(adresse, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-API-Key": cle },
  body: JSON.stringify(reading),
});
const data = await resp.json();
```

Le code distingue deux formes d'erreur : `detail` est un texte pour 401, 500 ou 503, mais une liste pour 422. La page affiche donc soit le message du serveur, soit le détail des champs refusés.

Essais dans le navigateur, page servie sur `http://localhost:5500` :

| Essai | Résultat affiché |
|---|---|
| Relevé normal, bonne clé | `Pas d'alerte : probabilité de panne 0.3 %` |
| 500 °C, bonne clé | `Erreur 422 : temperature_c : Input should be less than or equal to 150` |
| Relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide` |
| Valeurs par défaut, bonne clé | `ALERTE : probabilité de panne 94.8 %` |

### Expérience CORS

En servant la page sur le port 5501 au lieu de 5500, la page affiche :

```text
API injoignable (arrêtée, ou origine refusée par CORS) : Failed to fetch
```

La console du navigateur précise que l'origine `http://localhost:5501` n'est pas autorisée par la politique CORS.

`curl.exe` obtient pourtant une réponse avec la bonne clé. C'est normal : CORS est une règle appliquée par le navigateur, pas par l'API. Un outil en ligne de commande envoie directement la requête HTTP. La page est bloquée pour protéger l'utilisateur, mais l'API reste protégée par sa clé.

Une origine est le triplet protocole + hôte + port. `http://localhost:5500` et `http://localhost:8000` sont donc deux origines différentes.

## 6. Tests de l'activité 1 dans le TP2

En copiant `test_casser.py` dans `tp/tp2/tests` sans ajouter l'en-tête de clé, quatre tests échouent et un passe :

```text
4 failed, 1 passed
```

Les quatre échecs reçoivent 401 au lieu de 422, car la clé est vérifiée avant le corps de la requête. Le cinquième cas, la mauvaise route, passe quand même : `/v1/predire` n'existe pas, donc la requête s'arrête sur un 404 avant même d'atteindre le contrôle de la clé.

Avec `headers=HEADERS`, tous les tests passent :

```text
23 passed, 1 warning
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | santé, prédiction, alerte, validation, 503 |
| `tests/test_casser.py` | 5 | requêtes volontairement incorrectes |
| `tests/test_data.py` | 3 | données |
| `tests/test_security.py` | 5 | clé absente, fausse clé, CORS, configuration |
| `tests/test_train.py` | 3 | entraînement et artefacts |

## 7. Réponses aux questions

**1. Différence entre 401 et 422, puis entre 401 et 403 ?**  
401 signifie que l'appelant n'est pas authentifié : clé absente ou invalide. 422 signifie que l'appelant est accepté mais que ses données ne respectent pas le schéma. 403 signifie que l'appelant est identifié mais n'a pas le droit d'effectuer cette action.

**2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ?**  
Une clé écrite dans un fichier versionné reste dans l'historique Git, même si on la supprime plus tard. Il faudrait alors la changer. `.env` contient la vraie clé et reste en local ; `.env.example` contient les mêmes variables avec une valeur fictive et sert de modèle. C'est `.env.example` qui est commité.

**3. Pourquoi transmettre la clé dans un en-tête plutôt que dans l'URL ?**  
Les URL peuvent être enregistrées dans les journaux du serveur, l'historique du navigateur ou des outils de suivi. Un en-tête `X-API-Key` évite cette exposition. En production, HTTPS reste nécessaire pour protéger le contenu de la requête.

**4. Que fait `secrets.compare_digest` de plus qu'un `==` ?**  
La comparaison ne s'arrête pas au premier caractère différent. Avec `==`, un attaquant pourrait mesurer le temps de réponse pour deviner la clé caractère par caractère. `compare_digest` limite ce type de fuite.

**5. Qu'est-ce qu'une origine ?**  
C'est la combinaison du protocole, de l'hôte et du port. `http://localhost:5500` et `http://localhost:8000` ne sont pas la même origine, car le port change.

## 8. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier :** `tp/tp2`
- **Mon fichier :** `CR_TP2_Mazine_CHATER.md`
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp2`
- **Fichiers sensibles :** `.env` et `.venv` ne sont pas dans le dépôt
- **Vérification :** `.env` n'apparaît pas dans `git status` avant le commit

## 9. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| 401 pour une clé absente ou fausse | Le problème vient de l'appelant : il n'a pas fourni la bonne preuve d'identité. 401 est le code prévu pour une authentification absente ou invalide. |
| 500 quand la clé serveur n'est pas configurée | Le client peut avoir une clé parfaitement valide ; c'est le serveur qui n'a rien à comparer. Un 401 ferait porter au client une erreur de configuration qui n'est pas la sienne. |
| `secrets.compare_digest` avec `.encode()` | La comparaison ne s'arrête pas au premier caractère différent, ce qui limite les attaques temporelles. `encode()` transforme les chaînes en octets, la forme attendue par `compare_digest`. |
| Clé dans l'en-tête `X-API-Key` | Une URL se retrouve dans les journaux, l'historique du navigateur et les proxies. L'en-tête évite cette trace, même si HTTPS reste indispensable pour protéger le contenu. |
| `/health` accessible sans clé | La supervision et les tests de disponibilité doivent pouvoir l'appeler sans secret. La route ne révèle que l'état du service. |
| CORS limité à `http://localhost:5500` | Seule la page de développement doit pouvoir appeler l'API depuis un navigateur. Une origine `*` autoriserait n'importe quel site à tenter des requêtes ; la clé reste la protection de fond. |
| Middleware CORS côté API | C'est le navigateur qui bloque la réponse si l'API n'envoie pas les bons en-têtes. Le serveur doit donc répondre au preflight et autoriser explicitement l'origine. |
| Une clé de service plutôt qu'un compte utilisateur | Le TP porte sur un service interne appelé par une page et un script. Une clé partagée suffit et évite de gérer des utilisateurs, des mots de passe et des sessions. |
| Seulement `GET`, `POST`, `Content-Type` et `X-API-Key` | On n'autorise que les méthodes et les en-têtes réellement utilisés. C'est le principe du moindre privilège. |
| `.env` ignoré et `.env.example` versionné | Une clé commitée reste dans l'historique Git même après suppression. `.env.example` documente les variables sans exposer de secret. |
| `@pytest.mark.parametrize` | Une seule fonction décrit cinq cas, mais pytest les compte séparément. On voit immédiatement quel scénario échoue. |
| Tests sans en-tête, puis avec en-tête | Sans en-tête, les 422 deviennent des 401 : cela montre que l'authentification passe avant la validation. Le cas de la mauvaise route reste en 404, car le routage précède la sécurité. |
| Ruff et pytest séparés | Ruff vérifie la qualité du code sans l'exécuter ; pytest vérifie le comportement. Un code propre peut être faux, et un code qui passe les tests peut être mal écrit. |
| La page web gère deux formes de `detail` | Les erreurs 401, 500 et 503 renvoient un texte, alors que 422 renvoie une liste d'erreurs par champ. L'interface doit afficher les deux sans casser. |

## 10. Ce que je retiens

Le TP2 m'a surtout fait comprendre l'ordre des contrôles : une requête peut être refusée pour plusieurs raisons, mais c'est toujours le premier contrôle en échec qui produit la réponse. Cela explique les différences entre 401, 422 et 503.

Ce qui reste un peu flou pour moi, c'est le détail du préflight CORS. Je sais reconnaître le blocage dans la console et je sais pourquoi `curl` passe, mais je n'ai pas encore regardé en détail la requête `OPTIONS` échangée avant le `POST`. Je veux aussi revoir la configuration des origines autorisées pour ne pas laisser une liste trop large en production.
