# Documentation — TP3

## Pourquoi une interface ?

Une API JSON est pratique pour un programme, pas pour une personne qui veut
comprendre les données. Streamlit permet de construire une page interactive
en Python, sans écrire de HTML ni de JavaScript.

L'interface a deux rôles distincts :

1. **Explorer** : voir la répartition des pannes et le lien entre une mesure
   et le risque. C'est ce qui permet de juger si le modèle a du sens.
2. **Prédire** : envoyer un relevé et afficher le résultat de l'API.

## Pourquoi un client Python séparé ?

L'interface n'appelle pas `httpx` directement. Tout passe par
`MaintaiClient` :

- le format de la requête est écrit une seule fois ;
- les erreurs sont traduites en `APIError` avec un code et un message ;
- les tests peuvent remplacer le client par un faux, sans lancer de serveur.

C'est le même principe que le client web du TP2, mais en Python et
réutilisable depuis un notebook ou un script.

## Fonctionnement de l'interface

Streamlit réexécute tout le script à chaque interaction. Deux conséquences :

- la lecture du CSV est entourée de `@st.cache_data` pour ne pas la refaire
  à chaque clic ;
- l'état (URL, clé, valeurs des curseurs) est porté par les widgets, pas par
  des variables globales.

Les appels à l'API sont faits uniquement après un clic sur « Prédire » :
ouvrir la page ne dépend pas du serveur.

## Choix techniques

**Le client est injectable.** Le constructeur accepte un `httpx.Client`
existant. Les tests passent le `TestClient` de FastAPI : on teste le vrai
code du client sans ouvrir de port réseau.

**Les erreurs sont séparées.** Une erreur métier (`APIError`, par exemple
401 ou 422) affiche un avertissement avec le message du serveur. Une panne
réseau (`httpx.HTTPError`) affiche une erreur distincte : « API
injoignable ». L'utilisateur sait ainsi s'il doit corriger sa saisie ou
démarrer le serveur.

**Les graphiques restent simples.** Un histogramme et un nuage de points
suffisent pour ce TP. Une bibliothèque de graphiques plus lourde n'apporterait
rien ici.

## Limites

- L'interface ne conserve pas l'historique des prédictions.
- La clé API est saisie à la main à chaque session.
- Le nuage de points est un échantillon de 500 lignes pour rester fluide.
