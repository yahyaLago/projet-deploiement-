# Documentation — TP2

## Ce qui change par rapport au TP1

L'API fonctionnait, mais n'importe qui pouvait l'appeler depuis n'importe
quelle page. Le TP2 ajoute deux protections :

1. **Une clé API** : sans l'en-tête `X-API-Key` correct, les routes `/v1`
   répondent 401.
2. **CORS** : seules les origines déclarées peuvent appeler l'API depuis un
   navigateur.

Un client web statique (`web/index.html`) illustre l'usage : il envoie un
relevé, lit la réponse JSON et affiche la probabilité et l'alerte.

## Comment fonctionne la clé API

- La clé attendue est lue dans `MAINTAI_API_KEY`, jamais écrite dans le code.
- `require_api_key` est une dépendance FastAPI : elle s'exécute avant chaque
  route du routeur `/v1`.
- La comparaison utilise `secrets.compare_digest`, qui prend un temps
  constant et évite de laisser fuiter la clé par la durée de la réponse.
- Si le serveur n'a pas de clé configurée, il répond 500 : mieux vaut un
  service qui refuse de servir qu'un service ouvert par accident.

`/health` reste volontairement public : un outil de supervision doit pouvoir
vérifier que le service tourne sans connaître le secret.

## Comment fonctionne CORS

Un navigateur bloque par défaut une page servie par `localhost:5500` qui
appelle `localhost:8000`. Le serveur doit répondre avec l'en-tête
`Access-Control-Allow-Origin`. On déclare donc la liste blanche dans
`MAINTAI_CORS_ORIGINS`.

Une origine inconnue ne reçoit pas cet en-tête : le navigateur bloque la
réponse. C'est une protection contre les pages tierces, pas contre un client
qui appellerait l'API directement en dehors d'un navigateur — d'où l'intérêt
de garder la clé API.

## Choix techniques

**La clé dans un en-tête, pas dans l'URL.** Une clé en paramètre d'URL se
retrouve dans les journaux et l'historique du navigateur. L'en-tête
`X-API-Key` est le mécanisme attendu par `fetch`.

**Une dépendance plutôt qu'un test dans chaque route.** La vérification est
déclarée une fois sur le routeur. Ajouter une route protégée ne demande donc
aucun effort et on ne peut pas l'oublier.

**Pas encore de comptes utilisateurs.** Le TP demande une clé partagée. Un
vrai système demanderait une base d'utilisateurs, des clés par client et une
rotation ; c'est hors du périmètre.

## Limites

- Une seule clé pour tous les clients : impossible de révoquer un client
  sans changer la clé de tout le monde.
- La clé circule en clair si l'API n'est pas derrière HTTPS.
- Le client web garde la clé dans un champ de formulaire : elle n'est pas
  stockée, mais elle est visible dans le navigateur de l'utilisateur.
