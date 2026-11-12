# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Auteur :** Ahmed RAOUI  
**Groupe :** G1My  
**Date :** 05/11/2026  
**Dépôt GitHub :** https://github.com/yahyaLago/projet-deploiement-

---

## Introduction

Le TP2 de MaintAI porte sur les tests de robustesse d'une API de prédiction de panne, l'analyse statique du code avec Ruff, l'authentification par clé API et l'appel de l'API depuis une interface web. Ce compte rendu présente les principes techniques, les réponses aux questions du TP et les vérifications réalisées sur l'environnement de travail d'Ahmed RAOUI.

**Traçabilité des résultats :** les exécutions de `python -m pytest` et de `python -m ruff check .` dans `tp/tp2` ont été confirmées par des captures du terminal. Les tableaux de scénarios HTTP et CORS ci-dessous décrivent les comportements attendus ou illustrés par le compte rendu de référence fourni par le groupe ; ils ne constituent pas, à eux seuls, des preuves d'exécution individuelle.

---

## 1. Activité 1 — Casser son API (dans `tp/tp1`)

L'objectif de cette activité est d'envoyer à l'API des requêtes incorrectes afin de vérifier qu'elle refuse les données invalides sans planter.

| Requête de test | Problème introduit | Code HTTP attendu | Explication |
|---|---|---:|---|
| 1 | Absence du champ `load_pct` | 422 | Le corps de la requête ne respecte pas le schéma attendu. |
| 2 | `load_pct = 250` | 422 | La valeur dépasse les bornes autorisées. |
| 3 | `temperature_c = "chaud"` | 422 | Le champ numérique reçoit une chaîne de caractères non convertible. |
| 4 | Champ supplémentaire `couleur` | 422* | Le schéma refuse les champs supplémentaires lorsqu'il utilise `extra="forbid"`. |
| 5 | `POST /v1/predire` | 404 | La route demandée n'existe pas. |

*Le code 422 du scénario 4 suppose que le schéma `SensorReading` est configuré avec `extra="forbid"`, comme dans l'exemple de référence du groupe.*

**Une de ces prévisions peut-elle être fausse ? Pourquoi ?**  
Oui, si le schéma ou les routes de l'API sont configurés autrement. Par exemple, sans `extra="forbid"`, un champ supplémentaire pourrait être ignoré plutôt que rejeté. Les codes réellement retournés doivent être relevés lors de l'exécution des requêtes.

**À quoi sert `@pytest.mark.parametrize` ?**  
Ce décorateur permet d'exécuter une seule fonction de test pour plusieurs jeux de données. Avec cinq cas de test, Pytest compte cinq exécutions distinctes, ce qui rend les tests plus lisibles et facilite l'identification des erreurs.

**Vérification propre à `tp/tp1` :** le résultat final de ses tests n'a pas été relevé dans les captures transmises pour ce compte rendu ; il n'est donc pas présenté comme une exécution personnelle.

---

## 2. Analyse de la qualité du code avec Ruff

Ruff est un outil d'analyse statique qui détecte notamment les imports inutilisés, les problèmes d'organisation des imports et certaines mauvaises pratiques Python.

**Commande exécutée dans `tp/tp2` :**

```powershell
python -m ruff check .
```

**Résultat vérifié sur le terminal d'Ahmed RAOUI :**

```text
All checks passed!
```

**Différence entre Ruff et Pytest :**  
Ruff examine le code sans exécuter les fonctionnalités de l'application. Pytest exécute les tests et vérifie que le comportement du programme correspond aux assertions prévues. Les deux sont complémentaires : un code peut respecter les règles de Ruff sans être fonctionnel, ou réussir des tests tout en comportant des problèmes de style.

---

## 3. Mise en place du TP2 (dans `tp/tp2`)

La mise en place du TP2 consiste à préparer le projet, ses dépendances et les tests de sécurité. Avant l'activation de la vérification de la clé API, les scénarios « clé absente » et « clé incorrecte » peuvent échouer si l'API accepte encore les requêtes sans authentification.

**Quels sont les deux tests concernés dans l'exemple du TP ?**

- `test_missing_key_is_rejected` : vérifie le refus d'une requête sans clé.
- `test_wrong_key_is_rejected` : vérifie le refus d'une requête avec une mauvaise clé.

Dans l'état initial décrit par le document de référence du groupe, ces tests recevaient `200` au lieu du `401` attendu. Ce résultat initial n'a pas été reproduit séparément dans les captures d'Ahmed ; seul l'état final du TP2 a été vérifié.

---

## 4. Protection de l'API par une clé (sprint 1)

### 4.1. Principe de `require_api_key()`

La fonction de sécurité récupère la valeur de l'en-tête `X-API-Key`, puis la compare à la clé configurée côté serveur. Elle doit distinguer deux situations :

- **401 Unauthorized** : la clé est absente ou incorrecte.
- **500 Internal Server Error** : la clé attendue n'a pas été configurée sur le serveur.

Le principe d'implémentation utilisé dans le TP est le suivant :

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

### 4.2. Application de la sécurité aux routes

La fonction seule ne protège pas l'API. Il faut l'associer au routeur, par exemple :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

**Pourquoi les tests échouent-ils encore si l'on crée `security.py` sans modifier le routeur ?**  
Parce que la fonction de contrôle existe, mais n'est appelée par aucune route. L'ajout de `Depends(require_api_key)` permet de vérifier la clé avant de traiter une requête sur les routes protégées.

### 4.3. Scénarios HTTP à contrôler

| Scénario | Code attendu | Justification |
|---|---:|---|
| `GET /health` sans clé | 200 | La route de santé reste accessible si elle n'est pas protégée. |
| `POST /v1/predict` sans clé | 401 | Authentification manquante. |
| `POST /v1/predict` avec une mauvaise clé | 401 | Authentification invalide. |
| `POST /v1/predict` avec une bonne clé et des données valides | 200 | Requête acceptée. |
| `POST /v1/predict`, 500 °C, sans clé | 401 | Le contrôle de clé bloque d'abord la requête. |
| `POST /v1/predict`, 500 °C, avec une bonne clé | 422 | La validation refuse une température hors limites. |

**Pourquoi 500 °C sans clé et 500 °C avec la bonne clé ne donnent-ils pas le même code ?**  
Sans clé, l'API rejette d'abord la requête pour défaut d'authentification (`401`). Avec une clé valide, le corps de la requête peut être validé, et la température non autorisée provoque `422`.

**Pourquoi l'absence de configuration de la clé côté serveur doit-elle produire 500 plutôt que 401 ?**  
L'erreur vient du serveur qui ne possède aucune clé de référence, et non de l'identité de l'appelant. Un `401` attribuerait à tort le problème au client.

*Les codes de ce tableau présentent les scénarios du TP et leur logique. Les réponses HTTP individuelles n'ont pas été relevées dans les captures transmises.*

---

## 5. Appel de l'API depuis la page web (sprint 2)

L'interface web collecte les valeurs des capteurs, l'adresse de l'API et une clé d'accès. Une requête `fetch` envoie ensuite les données au serveur.

### 5.1. Exemple de requête `fetch`

```javascript
const response = await fetch(apiUrl + "/v1/predict", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": apiKey
  },
  body: JSON.stringify(reading)
});

const data = await response.json();
if (!response.ok) {
  // Afficher l'erreur HTTP et le détail renvoyé par l'API.
} else {
  // Afficher la probabilité de panne et l'état d'alerte.
}
```

Si la requête réussit, la page peut afficher une probabilité de panne ainsi qu'une alerte éventuelle. Si elle échoue, elle doit expliquer l'erreur : clé invalide (`401`), données non conformes (`422`) ou API injoignable.

### 5.2. Comprendre CORS

Une **origine** combine un protocole, un hôte et un port. Ainsi, `http://localhost:5500` et `http://localhost:8000` sont deux origines différentes, car leurs ports diffèrent.

Si le serveur n'autorise que l'origine `http://localhost:5500`, une page servie depuis `http://localhost:5501` peut être bloquée par le navigateur avec un message CORS, par exemple `Failed to fetch`. Le navigateur applique la politique CORS ; un outil comme `curl.exe` n'impose pas cette restriction de la même façon.

**Pourquoi `curl.exe` peut-il obtenir une réponse lorsque le navigateur bloque la page ?**  
Parce que CORS est un mécanisme de contrôle côté navigateur. Une requête HTTP directe peut parvenir à l'API même si l'origine de la page web n'est pas autorisée ; l'authentification par clé reste donc indispensable.

*Les essais visuels sur la page web et la console CORS ne sont pas attestés par les captures actuellement disponibles pour Ahmed.*

---

## 6. Tests de robustesse ajoutés au TP2

Lorsque les tests du TP1 sont repris dans le TP2, il faut tenir compte de l'authentification. Sans en-tête de clé, les requêtes vers une route existante et protégée peuvent retourner `401` avant d'atteindre la validation des données. En ajoutant un en-tête valide, les tests peuvent à nouveau vérifier les erreurs `422` attendues.

**Pourquoi le test de mauvaise route peut-il réussir même sans clé ?**  
Parce que le chemin inexistant renvoie `404`, avant toute exécution de la dépendance de sécurité d'une route qui n'a pas été trouvée.

### Résultat final de Pytest — vérifié

Commande exécutée dans `tp/tp2` :

```powershell
python -m pytest
```

Résultat obtenu dans le terminal d'Ahmed RAOUI :

```text
collected 23 items

tests/test_api.py .......          [ 30%]
tests/test_casser.py .....         [ 52%]
tests/test_data.py ...             [ 65%]
tests/test_security.py .....       [ 86%]
tests/test_train.py ...            [100%]

23 passed, 1 warning in 9.20s
```

**Interprétation :** les 23 tests du TP2 ont réussi. L'unique avertissement signalé concerne l'utilisation dépréciée de `starlette.testclient.TestClient` via FastAPI ; il ne constitue pas un échec de test.

---

## 7. Questions de compréhension

### 1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?

- **401 Unauthorized :** authentification absente ou invalide.
- **422 Unprocessable Content :** données de la requête refusées par les règles de validation.
- **403 Forbidden :** requête comprise, mais accès non autorisé, même lorsque l'identité de l'appelant est connue.

### 2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Quelle différence entre `.env` et `.env.example` ?

Une clé secrète inscrite dans le dépôt peut être exposée à d'autres personnes et rester présente dans l'historique Git. Le fichier `.env` contient les valeurs privées locales et doit être ignoré par Git. Le fichier `.env.example` présente uniquement des noms de variables et des valeurs fictives : il peut être versionné pour expliquer la configuration nécessaire.

### 3. Pourquoi la clé est-elle transmise dans un en-tête plutôt que dans l'URL ?

Une URL risque d'apparaître dans les journaux, l'historique ou les outils de suivi. Un en-tête `X-API-Key` évite de l'intégrer à l'URL, mais la communication doit également être protégée par HTTPS en production.

### 4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?

Cette fonction réduit le risque de divulgation d'informations par comparaison temporelle, car son comportement de comparaison est conçu pour éviter les différences de durée liées à la position d'un caractère incorrect. Cela la rend préférable à une comparaison ordinaire pour des secrets.

### 5. Qu'est-ce qu'une origine ? Les ports 5500 et 8000 constituent-ils la même origine ?

Une origine correspond au triplet **protocole + hôte + port**. `http://localhost:5500` et `http://localhost:8000` sont donc deux origines distinctes. Les échanges depuis le navigateur peuvent être soumis à CORS.

---

## 8. Rendu Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier du TP2 :** `tp/tp2`
- **Compte rendu individuel :** `tp/tp2/compte_rendu_TP2_Ahmed_RAOUI.md`
- **Branche principale :** `main`
- **Branche de préparation du compte rendu :** `tp2-ahmed-livrables`
- **État de la livraison individuelle :** fichier préparé ; commit, push et Pull Request à réaliser après vérification.
- **Précaution :** ne pas inclure `.env`, les environnements virtuels, les caches ou les clés d'API dans les livrables.

---

## 9. Ce qui reste flou / points à approfondir

Les points qui méritent une attention particulière sont l'ordre de traitement entre authentification et validation, le rôle exact de CORS et la différence entre l'analyse statique et les tests fonctionnels. L'exécution individuelle des scénarios HTTP et de l'expérience CORS permettra de compléter les preuves expérimentales si elles sont demandées dans le rendu.

---

## Conclusion

Le TP2 met en évidence trois composantes complémentaires d'une API fiable : **la validation des données**, **l'authentification des requêtes** et **les tests automatisés**. Les vérifications réellement effectuées dans l'environnement d'Ahmed RAOUI montrent **23 tests réussis sur 23** et **aucune anomalie détectée par Ruff**. Ces résultats confirment le bon état du projet lors de la vérification finale, sans remplacer les relevés HTTP détaillés qui pourraient être demandés séparément.
