# TP3 — MaintAI : une interface Streamlit

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 12/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp3`

---

## 1. Mise en place

Le starter du TP3 reprend le projet du TP2 et ajoute `maintai/client.py`, `ui/app.py`, `tests/test_client.py` et `tests/test_ui.py`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Au tout premier lancement, avant l'installation des dépendances, les tests du client ne démarrent pas :

```text
3 errors
ModuleNotFoundError: No module named 'fastapi'
```

Une fois `requirements.txt` installé, j'obtiens :

```text
5 failed, 18 passed, 1 warning
```

Les trois tests de `tests/test_client.py` échouent avec `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`. Les deux tests de `tests/test_ui.py` échouent avec `IndexError: list index out of range`, car les éléments attendus dans l'interface ne sont pas encore tous présents.

Après avoir écrit les deux sprints, les 23 tests passent.

## 2. Lancer Streamlit

La commande `streamlit run ui/app.py` dépend de l'exécutable `streamlit` présent dans le `PATH`. Si l'environnement virtuel n'est pas activé, ou si un autre Python est utilisé, elle peut échouer ou lancer une mauvaise version.

La commande fiable est :

```powershell
python -m streamlit run ui/app.py
```

`python -m streamlit` exécute le module Streamlit de l'interpréteur courant, c'est-à-dire celui de `.venv` quand l'environnement est activé.

La page s'ouvre sur `http://localhost:8501`. Elle affiche le titre « MaintAI · prédiction de panne », une barre latérale avec l'URL de l'API et la clé, puis deux onglets : « Données » et « Prédiction ».

## 3. Sprint 1 : l'onglet Données

Le code de l'onglet dans `ui/app.py` :

```python
df = charger(get_settings().data_path)

n_rows = len(df)
failure_rate = df["failure"].mean()
avg_temp = df["temperature_c"].mean()

cols = st.columns(3)
cols[0].metric("Relevés", n_rows)
cols[1].metric("Taux de panne", f"{failure_rate * 100:.1f} %")
cols[2].metric("Température moyenne", f"{avg_temp:.1f} °C")

feature = st.selectbox("Variable à analyser", FEATURES)
bins = pd.qcut(df[feature], q=5, duplicates="drop")
taux_par_tranche = (
    df.assign(_tranche=bins)
    .groupby("_tranche")["failure"]
    .mean()
    .mul(100)
    .rename("taux_panne")
    .to_frame()
)
taux_par_tranche.index = taux_par_tranche.index.map(str)
st.bar_chart(taux_par_tranche)

st.scatter_chart(df, x="temperature_c", y="vibration_mm_s", color="failure")
```

Avec les 5 000 relevés synthétiques de `data/sensors.csv` :

| Indicateur | Valeur |
|---|---:|
| Relevés | 5 000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

En choisissant `vibration_mm_s`, le taux de panne augmente nettement d'une tranche à l'autre :

| Tranche de vibration (mm/s) | Taux de panne |
|---|---:|
| 0,019 – 1,26 | 1,3 % |
| 1,26 – 2,08 | 2,3 % |
| 2,08 – 3,00 | 5,7 % |
| 3,00 – 4,48 | 12,9 % |
| 4,48 – 22,23 | 45,8 % |

La vibration pèse donc plus que la température. Le nuage de points le confirme : les pannes se concentrent vers les vibrations élevées. C'est cohérent avec `dataset.py`, où le coefficient associé à la vibration est le plus fort dans le calcul du risque.

**Le test du `print("relance")`.** En plaçant un `print` en haut du fichier, il réapparaît dans le terminal à chaque interaction. Streamlit réexécute tout le script de haut en bas à chaque relance. En revanche, les champs du formulaire de prédiction ne déclenchent rien tant que le bouton « Prédire » n'est pas cliqué, car ils sont dans un `st.form`. J'ai retiré le `print` après le test.

**À quoi sert `@st.cache_data` ?** Sans ce décorateur, le CSV serait relu à chaque relance, même si rien n'a changé. Le cache garde le DataFrame en mémoire pour le même chemin de fichier. Si le fichier est régénéré sans changer de nom, il faut vider le cache pour voir les nouvelles données.

## 4. Sprint 2 : l'onglet Prédiction

Le client `maintai/client.py` fait en Python ce que le `fetch` du TP2 faisait en JavaScript :

```python
headers = None
if self.api_key is not None:
    headers = {"X-API-Key": self.api_key}

r = self.http.post("/v1/predict", json=reading, headers=headers)

if r.status_code != 200:
    try:
        payload = r.json()
    except ValueError:
        payload = {"detail": r.text}
    detail = payload.get("detail") if isinstance(payload, dict) else payload
    raise APIError(r.status_code, detail)

return r.json()
```

Le point important est `self.http.post` et non `httpx.post` : les tests injectent leur propre client dans `http`, ce qui permet de tester sans lancer uvicorn.

Dans l'interface, une erreur `APIError` est affichée avec `st.warning`, car l'API a répondu mais a refusé la requête. Une erreur `httpx.HTTPError` est affichée avec `st.error`, car l'API est injoignable.

À la fin du sprint 2 :

```text
23 passed, 1 warning
```

| Fichier | Tests | Ce qu'ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | API FastAPI |
| `tests/test_client.py` | 3 | `MaintaiClient` sans serveur |
| `tests/test_data.py` | 3 | données |
| `tests/test_security.py` | 5 | clé API et CORS |
| `tests/test_train.py` | 3 | artefacts du modèle |
| `tests/test_ui.py` | 2 | page Streamlit avec `AppTest` |

L'avertissement vient de `fastapi.testclient` et d'`httpx` ; il n'empêche aucun test de passer.

Essais dans Streamlit, avec l'API sur le port 8001 et la clé du fichier `.env` :

| Essai | Résultat affiché |
|---|---|
| Valeurs par défaut (72 °C, 6 mm/s, 85 %, 15 000 h), bonne clé | Probabilité de panne **95 %** et message d'alerte au seuil de 30 % |
| Valeurs par défaut, fausse clé | `Erreur 401 : Clé API absente ou invalide` |
| API arrêtée | `API injoignable : ...` |
| API lancée sans `MAINTAI_API_KEY` | `Erreur 500 : MAINTAI_API_KEY n'est pas configurée sur le serveur` |

### Pourquoi CORS ne bloque pas Streamlit

Le port 8501 n'est pas dans la liste des origines autorisées, et pourtant la prédiction fonctionne.

Dans le TP2, c'était le JavaScript du navigateur qui appelait directement l'API : CORS s'appliquait. Ici, le navigateur ne parle qu'à Streamlit. C'est le processus Python de Streamlit qui appelle ensuite FastAPI avec `MaintaiClient` et `httpx`. Cette requête de serveur à serveur ne passe pas par la politique CORS du navigateur.

## 5. Réponses aux questions

**1. Qui envoie la requête à l'API dans le TP2, et qui l'envoie dans le TP3 ?**  
Dans le TP2, c'est le JavaScript de la page, avec `fetch`. Dans le TP3, c'est le processus Streamlit, avec `MaintaiClient` et `self.http.post`.

**2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?**  
La fixture crée un `TestClient` FastAPI et le passe à `MaintaiClient(..., http=client)`. La requête est traitée dans le même processus, sans passer par un port réseau. `test_ui.py` va plus loin : `AppTest` exécute la page sans navigateur et `monkeypatch` remplace la prédiction par une réponse fixe.

**3. Streamlit ou page HTML/JavaScript pour une démonstration ? Et pour un technicien ?**  
Pour une démonstration rapide, Streamlit est plus pratique : les graphiques et les métriques s'écrivent en Python, sans JavaScript. Pour une application destinée à un technicien, une page HTML/JS ou une application dédiée offre plus de contrôle sur l'apparence, l'authentification et le déploiement. Streamlit reste un bon outil de prototypage.

## 6. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier :** `tp/tp3`
- **Mon fichier :** `CR_TP3_Mazine_CHATER.md`
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp3`
- **Fichiers exclus :** `.env`, `data/*.csv`, `models/` et `.venv`
- **ADR :** `docs/adr/004-interface-streamlit.md`

## 7. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| Streamlit pour la démonstration | L'équipe code en Python et Streamlit fournit les widgets, les graphiques et le cache sans écrire de JavaScript. C'est le bon outil pour un prototype présenté rapidement. |
| `python -m streamlit` plutôt que `streamlit run` | La commande utilise l'interpréteur courant, donc le Streamlit installé dans `.venv`. `streamlit run` dépend du `PATH` et peut appeler un autre environnement. |
| Deux onglets « Données » et « Prédiction » | Les deux usages sont séparés sans cacher l'un derrière l'autre : on consulte le jeu, puis on teste un relevé. |
| Indicateurs nombre de relevés, taux de panne, température moyenne | Trois chiffres donnent un résumé immédiat du jeu avant les graphiques détaillés. |
| `pd.qcut(q=5)` plutôt que `pd.cut` | Les tranches de quantiles contiennent à peu près le même nombre de relevés, ce qui rend les taux comparables et évite les tranches vides. Un `cut` à largeur fixe peut concentrer presque toutes les valeurs dans une seule tranche. |
| `duplicates="drop"` | Certaines variables, comme `load_pct`, ont beaucoup de valeurs répétées. Sans cette option, le calcul des quantiles peut produire des bornes identiques et échouer. |
| Graphique en barres du taux de panne | Le taux par tranche répond directement à la question « où le risque augmente-t-il ? ». Un simple comptage serait dominé par les tranches les plus nombreuses. |
| Nuage température / vibration coloré par `failure` | Il montre les deux signaux principaux et la séparation des pannes. On voit que les points de panne se concentrent aux vibrations élevées. |
| `st.form` pour le relevé | Les curseurs sont envoyés ensemble au clic sur « Prédire ». Sans formulaire, chaque déplacement relancerait le script et pourrait déclencher une requête inutile. |
| `@st.cache_data` sur `charger` | Streamlit réexécute tout le script à chaque interaction. Le cache évite de relire le CSV à chaque fois. Il est indexé par le chemin : si le fichier change sans changer de nom, il faut vider le cache. |
| URL et clé dans la barre latérale | On peut viser une autre instance de l'API ou changer de clé sans modifier le code. |
| Chemin du CSV lu depuis la configuration | `get_settings().data_path` permet de changer de fichier par variable d'environnement, sans toucher à l'interface. |
| `MaintaiClient` avec un client `http` injectable | Les tests passent un `TestClient` à la place d'un vrai client HTTP. Le même code fonctionne sans uvicorn en test et avec `httpx` en production. |
| `self.http.post` plutôt que `httpx.post` | Appeler `httpx.post` directement ignorerait le client injecté par les tests. |
| `APIError` distinct de `httpx.HTTPError` | Le premier signifie que l'API a répondu et refusé ; le second que le réseau ou le serveur est injoignable. L'interface peut afficher un avertissement ou une erreur adaptée. |
| Probabilité affichée en pourcentage entier | La probabilité est déjà une estimation. Afficher 95 % est plus lisible que 94,75 % et évite une fausse impression de précision. |
| Pas de blocage CORS pour Streamlit | Le navigateur ne parle qu'à Streamlit. C'est le processus Python qui appelle l'API, et CORS ne s'applique pas aux échanges serveur à serveur. |

## 8. Ce que je retiens

Le TP3 m'a fait comprendre la séparation entre l'interface et le modèle. Streamlit ne calcule rien lui-même : il affiche les données et délègue la prédiction à l'API. C'est ce qui permet de changer l'interface sans toucher au modèle.

Ce qui reste à approfondir : le comportement du cache quand le fichier CSV est régénéré, et la manière de déployer Streamlit ailleurs qu'en local. Pour l'instant, je sais le faire fonctionner sur ma machine, mais je n'ai pas encore testé un accès à distance ni plusieurs utilisateurs simultanés.
