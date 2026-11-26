# ADR 004 : une interface Streamlit pour MaintAI

Date : 12/11/2026 · Auteur : Yahya Baid

Séance 6 · Une interface (TP3)

## Contexte

Un technicien de maintenance doit voir les données et demander une prédiction sans écrire de requête HTTP. L’API du TP2 est déjà protégée par une clé, et une page HTML/JavaScript l’appelle déjà. Il faut un troisième client, écrit en Python, livrable en une séance, avec des graphiques et un formulaire.

## Options étudiées

1. **Page HTML + JavaScript (TP2)** : déjà en place, contrôle total du design, mais chaque graphique et chaque contrôle se code à la main. CORS s’applique : le navigateur envoie `fetch` vers l’API.
2. **Streamlit (`ui/app.py`)** : un script Python devient une page. `st.metric`, `st.bar_chart`, `st.tabs` et `st.form` suffisent pour les deux onglets. Le serveur Streamlit appelle l’API via `MaintaiClient` : CORS ne s’applique pas. L’équipe n’a pas à écrire de JavaScript. Contrepartie : moins de liberté sur le look, et tout le script est relancé à chaque interaction.
3. **Interface desktop (Java, déjà vue)** : utile pour un client lourd, trop lourde pour une démo de 65 minutes avec graphiques.

## Décision

Streamlit est retenu pour le TP3, parce que l’interface doit être prête en une séance, que l’équipe programme déjà en Python, et que l’onglet « Données » a besoin de métriques et de graphiques sans JavaScript. On renonce à une page personnalisée pour le technicien ; la page web du TP2 reste le client navigateur.

L’onglet « Prédiction » n’appelle pas le modèle en local : il passe par l’API (`POST /v1/predict` + en-tête `X-API-Key`). Ainsi la clé, le schéma et le seuil restent ceux du TP2.

## Conséquences

- Lancement : `python -m streamlit run ui/app.py` (le module du `.venv` courant), et non `streamlit run` s’il pointe vers un autre Python.
- `@st.cache_data` sur `charger` évite de relire le CSV à chaque relance ; `st.form` évite de relancer à chaque curseur.
- Le port 8501 n’a pas à figurer dans `MAINTAI_CORS_ORIGINS`.
- Les tests `test_ui.py` exécutent la page avec `AppTest`, sans navigateur ; `test_client.py` injecte `TestClient` dans `MaintaiClient`, sans uvicorn.
- Une interface produit plus soignée pourrait remplacer Streamlit plus tard, sans changer l’API.
