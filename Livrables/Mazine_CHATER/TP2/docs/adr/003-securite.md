# ADR 003 — Sécurité de l'API

## Contexte

L'API du TP1 accepte toutes les requêtes. N'importe quelle page web pourrait
l'appeler à l'insu de l'utilisateur, et le service serait exposé dès qu'il
quitte le poste de développement.

## Décision

- Exiger une clé API dans l'en-tête `X-API-Key` sur toutes les routes `/v1`.
- Comparer la clé avec `secrets.compare_digest`.
- Limiter les origines CORS à une liste blanche configurable.
- Laisser `/health` public.

## Pourquoi

- Une clé partagée est le mécanisme le plus simple qui apporte une vraie
  barrière, sans introduire de base d'utilisateurs.
- `compare_digest` évite une attaque temporelle : le temps de réponse ne
  dépend pas du nombre de caractères corrects.
- CORS protège les utilisateurs contre les appels depuis des pages tierces ;
  la clé API protège le service contre les appels directs non autorisés.
- Une route de santé publique est nécessaire pour superviser le service.

## Conséquences

- Le fichier `.env` contient un secret : il est ignoré par Git et par
  l'image Docker.
- Si la variable `MAINTAI_API_KEY` manque, l'API répond 500 au lieu de
  s'ouvrir silencieusement.
- Les clients doivent envoyer l'en-tête, y compris le client web du TP2.

## Alternatives écartées

- **Clé dans l'URL** : visible dans les journaux, l'historique et les
  proxys.
- **JWT et comptes utilisateurs** : surdimensionné pour ce TP.
- **CORS ouvert (`*`)** : annulerait la protection navigateur.
