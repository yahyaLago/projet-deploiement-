# ADR 003 : transmission de la clé API et origines autorisées

Date : 05/11/2026 · Auteurs : Yahya

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés, et la clé ne doit apparaître ni dans le code ni dans Git. Une page web servie sur `http://localhost:5500` doit pouvoir appeler l'API, et une page servie ailleurs ne le doit pas.

## Options étudiées

### Où transmettre la clé
1. **En-tête `X-API-Key`** : n'apparaît pas dans l'URL, ne change pas le schéma du relevé, se vérifie avant de lire les données. Le client doit savoir ajouter un en-tête, et l'en-tête personnalisé déclenche une requête CORS préliminaire.
2. **Dans l'URL (`?key=...`)** : très simple à tester, mais l'URL est enregistrée dans les journaux du serveur et l'historique du navigateur. La clé y fuiterait.
3. **Dans le corps JSON** : absente des journaux d'URL, mais elle mélange authentification et données métier. Il faudrait l'ajouter au schéma `SensorReading` (qui refuse les champs en trop) et lire le corps avant de pouvoir refuser l'appelant.

### Quelles origines autoriser
1. **Liste explicite, lue dans `.env` (`MAINTAI_CORS_ORIGINS`)** : seules les pages prévues passent, et on change la liste sans toucher au code. Il faut relancer uvicorn après chaque modification.
2. **`*` (toutes les origines)** : plus rien à configurer, mais n'importe quel site pourrait appeler l'API depuis le navigateur de l'utilisateur.
3. **Liste écrite dans le code** : aussi stricte que `.env`, mais il faudrait modifier le code et redéployer pour chaque environnement.

## Décision
- **La clé voyage dans l'en-tête `X-API-Key`.** La raison principale : c'est la seule option qui la garde hors des URL et hors du schéma des données. L'URL ferait perdre la confidentialité de la clé, le corps ferait perdre la séparation entre contrôle d'accès et validation (401 avant 422).
- **Les origines sont une liste explicite, configurée dans `.env`** : `http://localhost:5500` et `http://127.0.0.1:5500`. `*` ferait perdre le refus de l'origine inconnue exigé par le projet. Une liste dans le code ferait perdre la possibilité de changer de configuration sans modifier le code.

## Conséquences
- `.env` reste hors de Git (`.gitignore`) et `.env.example` documente les variables avec une fausse valeur. Une clé commitée par erreur doit être changée, car elle reste dans l'historique.
- Sans clé configurée, l'API répond 500 sur `/v1` : elle ne s'ouvre jamais par défaut. `/health` reste public.
- CORS est une règle du navigateur et ne protège pas l'API contre `curl.exe` ou un programme Java. Seule la clé joue ce rôle.
- Une clé saisie dans une page web reste visible par son utilisateur. Il faudra revoir ce point avant une mise en production. Le transport devra aussi passer en HTTPS, car l'en-tête circule en clair en HTTP.
