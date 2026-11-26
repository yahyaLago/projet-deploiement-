# ADR 004 — Interface Streamlit

## Contexte

L'API est utilisable avec `curl` ou un client web, mais ces outils ne
montrent pas les données et demandent de connaître le format JSON. Pour
valider le modèle auprès d'un utilisateur métier, il faut une interface
lisible et interactive.

## Décision

Construire l'interface avec Streamlit, dans `ui/app.py`, et passer tous les
appels HTTP par `maintai/client.py`.

## Pourquoi

- Streamlit produit une page interactive en Python pur : pas de chaîne de
  build JavaScript à maintenir pour un TP.
- Le script peut lire directement le CSV et afficher des graphiques.
- Un client Python séparé évite de dupliquer la logique HTTP et permet de
  tester l'interface avec un faux client.

## Conséquences

- L'interface dépend de l'API : sans serveur, l'onglet « Données » fonctionne
  mais l'onglet « Prédiction » affiche une erreur explicite.
- Streamlit réexécute le script à chaque interaction : les lectures coûteuses
  doivent être mises en cache.
- L'interface n'est pas un produit fini : pas d'authentification des
  utilisateurs, pas d'historique.

## Alternatives écartées

- **Page HTML/JS maison** : déjà utilisée au TP2, mais plus longue à faire
  évoluer et moins pratique pour afficher des graphiques.
- **Notebook** : utile pour explorer, mais ne donne pas une application
  lançable et testable.
