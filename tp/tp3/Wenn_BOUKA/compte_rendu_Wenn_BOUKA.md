# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Auteur :** Wenn BOUKA  
**Groupe :** G1  
**Date :** 20/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp3/Wenn_BOUKA`

---

## 1. Mise en place (dans `tp/tp3/Wenn_BOUKA`)

Mon dossier reprend l'API protégée du TP2 et ajoute le client Python `maintai/client.py`, l'interface `ui/app.py` et leurs tests (`tests/test_client.py`, `tests/test_ui.py`).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Avec les `TODO` encore vides, `pytest` donne :

```text
FAILED tests/test_client.py::test_client_returns_prediction - NotImplementedError
FAILED tests/test_client.py::test_client_wrong_key_raises_401 - NotImplementedError
FAILED tests/test_client.py::test_client_bad_reading_raises_422 - NotImplementedError
FAILED tests/test_ui.py::test_ui_shows_the_data - IndexError: list index out of range
FAILED tests/test_ui.py::test_ui_shows_the_prediction - IndexError: list index out of range
5 failed, 18 passed, 1 warning
```

Les 18 tests hérités du TP2 passent. `test_client.py` échoue parce que `predict()` n'est pas écrite ; `test_ui.py` échoue sur `at.metric[0]` parce que la page n'affiche encore aucun indicateur.

## 2. Lancer Streamlit

**`streamlit run ui/app.py`** : la commande n'est trouvée que si l'exécutable `streamlit` du `.venv` est dans le `PATH`. Dans un terminal où le `.venv` n'est pas activé, j'obtiens `streamlit: No such file or directory` (et sous Windows « n'est pas reconnu… »). Pire, si un autre Python a Streamlit, c'est lui qui serait lancé, sans `maintai` ni les bonnes versions.

**`python -m streamlit run ui/app.py`** fonctionne toujours : `python -m` lance le module Streamlit **de l'interpréteur qu'on appelle**, donc celui du `.venv`. C'est la commande que je retiens.

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

La page affiche le titre « MaintAI · prédiction de panne », la barre latérale (URL de l'API, clé API) et deux onglets, « Données » et « Prédiction ».

## 3. Sprint 1 : l'onglet « Données »

```python
with onglet_donnees:
    df = charger(get_settings().data_path)

    # 1. Trois indicateurs côte à côte
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    # 2. La variable à analyser
    variable = st.selectbox("Variable", FEATURES)

    # 3. Taux de panne par quartile : 4 tranches de même effectif,
    #    pour que chaque barre repose sur autant de relevés
    quartiles = pd.qcut(df[variable], q=4, duplicates="drop")
    taux = df.groupby(quartiles, observed=True)["failure"].mean().mul(100).rename("taux de panne (%)")
    taux.index = taux.index.astype(str)
    st.caption(f"Taux de panne (%) par quartile de {variable}")
    st.bar_chart(taux)

    # 4. Nuage température / vibration, coloré par panne
    st.scatter_chart(df, x="temperature_c", y="vibration_mm_s", color="failure")
```

**Choix des tranches.** J'ai pris des **quartiles** (`pd.qcut`, 4 tranches de 1 250 relevés) plutôt que des tranches de largeur égale (`pd.cut`). Avec `pd.cut`, les tranches des extrêmes contiennent très peu de relevés et leur taux de panne saute d'un tirage à l'autre ; avec des quartiles, chaque barre repose sur le même nombre de relevés.

| Indicateur | Valeur affichée |
|---|---:|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

**`vibration_mm_s` contre `temperature_c` : laquelle compte le plus ?**

| Quartile de `temperature_c` | Taux de panne | Quartile de `vibration_mm_s` | Taux de panne |
|---|---:|---|---:|
| (23,5 ; 53,1] | 5,6 % | (0,02 ; 1,47] | 1,3 % |
| (53,1 ; 60,0] | 9,1 % | (1,47 ; 2,51] | 3,7 % |
| (60,0 ; 66,3] | 15,2 % | (2,51 ; 4,02] | 9,4 % |
| (66,3 ; 94,5] | 24,6 % | (4,02 ; 22,23] | **40,0 %** |

Les deux variables font monter le risque, mais la vibration beaucoup plus : on passe de 1,3 % à 40 % (×30) contre 5,6 % à 24,6 % (×4,4) pour la température. Le nuage de points le montre aussi : les pannes se regroupent en haut du graphique (fortes vibrations), à toutes les températures.

**`print("relance")` en haut de `ui/app.py`.** J'ai compté les lignes `relance` dans le terminal de Streamlit :

| Action | Nombre de `relance` |
|---|---:|
| ouverture de la page | 1 |
| changement de variable dans la liste | 2 |
| 5 déplacements d'un curseur de l'onglet « Prédiction » | 2 (inchangé) |

Streamlit **réexécute tout le script** à chaque interaction avec un widget. Les curseurs de la prédiction ne relancent rien parce qu'ils sont dans un `st.form` : rien n'est envoyé avant le clic sur « Prédire ». (Le `print` a été retiré ensuite.)

**`@st.cache_data` sur `charger` ?** Puisque le script tourne à chaque clic, sans cache le CSV serait relu à chaque fois. Avec le cache, le DataFrame est gardé en mémoire pour un même argument (`path`). Revers : si le fichier change sur le disque sans changer de nom, il faut vider le cache (menu ⋮ → *Clear cache*) pour voir les nouvelles données.

## 4. Sprint 2 : l'onglet « Prédiction »

### Le client — `maintai/client.py`

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    # La clé ne part que si elle est donnée : sans clé, l'API répondra 401
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)

    if r.status_code != 200:
        # 401/500/503 : detail est un texte ; 422 : une liste d'erreurs Pydantic.
        # Si le corps n'est pas du JSON (proxy, page d'erreur), on garde le texte brut.
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        raise APIError(r.status_code, detail)

    return r.json()
```

C'est le `fetch` du TP2 traduit en Python. J'utilise `self.http.post` et non `httpx.post` : les tests injectent leur `TestClient` dans `http=`, et c'est ce qui permet de tester le client sans serveur. J'ai ajouté le cas d'un corps qui n'est pas du JSON pour qu'une page d'erreur d'un proxy ne fasse pas planter l'interface.

### L'appel dans `ui/app.py`

```python
if envoye:
    try:
        resultat = MaintaiClient(url, api_key=cle or None).predict(releve)
    except APIError as e:
        st.warning(f"Erreur {e.status_code} : {e.detail}")
    except httpx.HTTPError as e:
        st.error(f"API injoignable ({url}) : {e}")
    else:
        pct = round(resultat["failure_probability"] * 100)
        seuil = round(resultat["threshold"] * 100)
        st.metric("Probabilité de panne", f"{pct} %")
        if resultat["alert"]:
            st.error(f"ALERTE : probabilité de panne {pct} % (seuil {seuil} %)")
        else:
            st.success(f"Pas d'alerte : probabilité de panne {pct} % (seuil {seuil} %)")
```

Les deux familles d'erreurs sont séparées : `APIError` (l'API a répondu, mais refuse) et `httpx.HTTPError` (personne n'a répondu). J'affiche le seuil renvoyé par l'API plutôt qu'un 30 % écrit en dur : si le seuil change côté serveur, l'interface suit.

### Fin du sprint 2

```text
tests/test_api.py .......              [ 30%]
tests/test_client.py ...               [ 43%]
tests/test_data.py ...                 [ 56%]
tests/test_security.py .....           [ 78%]
tests/test_train.py ...                [ 91%]
tests/test_ui.py ..                    [100%]

23 passed, 1 warning
```

L'avertissement est un `StarletteDeprecationWarning` de `fastapi.testclient`, sans lien avec mon code. `ruff check .` : `All checks passed!`

### Essais dans Streamlit

```bash
uvicorn maintai.api.main:app --env-file .env       # terminal 1, port 8000
python -m streamlit run ui/app.py                  # terminal 2, port 8501
```

Valeurs par défaut du formulaire : 72 °C, 6 mm/s, 85 %, 15 000 h.

| Essai | Ce qu'affiche Streamlit |
|---|---|
| bonne clé | métrique **95 %** et `ALERTE : probabilité de panne 95 % (seuil 30 %)` |
| fausse clé | `Erreur 401 : Clé API absente ou invalide` |
| API arrêtée (Ctrl+C sur uvicorn) | `API injoignable (http://localhost:8000) : [Errno 111] Connection refused` |
| API lancée sans `--env-file .env` | `Erreur 500 : MAINTAI_API_KEY n'est pas configurée sur le serveur` |

Captures : [`docs/captures/onglet_donnees.png`](docs/captures/onglet_donnees.png) et [`docs/captures/onglet_prediction.png`](docs/captures/onglet_prediction.png).

### Pourquoi pas de problème CORS ?

Le port 8501 ne figure pas dans `MAINTAI_CORS_ORIGINS`, et la prédiction fonctionne quand même. Au TP2, c'était le **navigateur** qui envoyait `fetch` vers l'API, et le navigateur applique CORS. Ici, le navigateur ne parle qu'à Streamlit ; c'est le **processus Python** de Streamlit qui appelle l'API avec httpx. Une requête de serveur à serveur n'est pas soumise à CORS, exactement comme curl au TP2.

## 5. Questions de compréhension

**1. Qui envoie la requête à l'API ?**  
TP2 : le JavaScript de la page, exécuté dans le navigateur de l'utilisateur. TP3 : le serveur Streamlit, en Python, via `MaintaiClient`. Conséquence : au TP2 la clé transite par le navigateur ; au TP3 elle est saisie dans la page mais c'est le serveur qui l'envoie.

**2. Pourquoi `test_client.py` n'a pas besoin d'uvicorn ?**  
La fixture crée un `TestClient` FastAPI et le passe à `MaintaiClient(..., http=client)`. Les requêtes sont traitées dans le même processus, sans réseau. De même, `test_ui.py` exécute la page avec `AppTest` sans navigateur, et remplace `MaintaiClient.predict` par une réponse connue avec `monkeypatch`.

**3. HTML + JS ou Streamlit ?**  
Pour **une démonstration à un client** : Streamlit. En une séance on a des indicateurs, des graphiques et un formulaire, sans écrire de JavaScript. Pour **l'application d'un technicien** utilisée tous les jours : une vraie page web (ou une appli mobile), qui donne la main sur l'ergonomie, l'authentification des utilisateurs, le fonctionnement hors ligne et le déploiement. Streamlit relance tout le script à chaque clic, ce qui devient limitant quand l'interface grossit.

Ma décision est détaillée dans [`docs/adr/004-interface-streamlit.md`](docs/adr/004-interface-streamlit.md).

## 6. Point Git

- **Mon dossier :** `tp/tp3/Wenn_BOUKA/`, avec le projet complet et ce compte rendu
- **Branche :** `tp-wenn-bouka`, pull request vers `main`
- **Exclus :** `.env`, `.venv`, `data/*.csv`, `models/` (voir `.gitignore` du dossier)

## 7. Ce qui reste flou

- Le cache `@st.cache_data` est partagé entre tous les utilisateurs de l'application : c'est parfait pour un CSV commun, mais je ne sais pas encore comment Streamlit isole les données propres à chaque utilisateur (`st.session_state`).
- La clé saisie dans la barre latérale est reconstruite à chaque relance ; je n'ai pas vérifié si elle apparaît dans les journaux de Streamlit.
