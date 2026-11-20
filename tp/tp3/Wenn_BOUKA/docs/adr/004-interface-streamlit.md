# ADR 004 : une interface Streamlit pour MaintAI

Date : 20/11/2026 · Auteur : Wenn BOUKA

## Contexte

Un technicien doit pouvoir explorer les relevés et demander une prédiction sans écrire de requête HTTP. L'API du TP2 est protégée par une clé et a déjà un client navigateur (page HTML + JavaScript). Il faut une interface plus riche (indicateurs, graphiques), livrable en une séance par une équipe qui code en Python.

## Options étudiées

1. **Enrichir la page HTML + JavaScript du TP2.** Contrôle total de l'affichage, mais chaque graphique et chaque contrôle se code à la main, en JavaScript. CORS s'applique.
2. **Streamlit (`ui/app.py`).** Un script Python devient une page : `st.metric`, `st.bar_chart`, `st.tabs`, `st.form` couvrent les deux onglets. Le serveur Streamlit appelle l'API avec `MaintaiClient`, donc sans CORS. Contreparties : apparence peu personnalisable, script entièrement relancé à chaque interaction.
3. **Charger le modèle directement dans Streamlit**, sans passer par l'API. Plus simple, mais on dupliquerait la validation, la clé et le seuil, et deux chemins de prédiction pourraient diverger.

## Décision

Streamlit, en passant **par l'API** (`POST /v1/predict` avec `X-API-Key`). L'interface est prête en une séance, reste en Python, et la validation, la clé et le seuil restent à un seul endroit : l'API du TP2.

## Conséquences

- Lancement avec `python -m streamlit run ui/app.py`, pour utiliser le Streamlit du `.venv`.
- `@st.cache_data` évite de relire le CSV à chaque relance ; `st.form` évite une relance à chaque mouvement de curseur.
- Le port 8501 n'a pas à être ajouté à `MAINTAI_CORS_ORIGINS`.
- L'interface affiche le seuil renvoyé par l'API au lieu d'une valeur écrite en dur.
- Pour une application de terrain utilisée au quotidien, une interface dédiée pourra remplacer Streamlit sans toucher à l'API.
