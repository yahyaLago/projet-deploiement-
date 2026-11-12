# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Auteur :** Yahya Baid
**Email :** yahya04ba@gmail.com
**Groupe :** G1My
**Date :** 12/11/2026

---

## 1. Mise en place (dans `TP/TP3`)

Le starter du TP3 reprend l’API du TP2 et ajoute `maintai/client.py`, `ui/app.py`, `tests/test_client.py` et `tests/test_ui.py`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Lors du premier lancement de `python -m pytest`, les dépendances n’étaient pas encore installées. La dernière ligne indiquait :

```text
3 errors in 2.48s
```

**Quels fichiers de tests échouent, et quelle erreur donnent-ils ?**

Les trois tests de `tests/test_client.py` n’ont pas pu démarrer. Leur fixture importe `fastapi.testclient`, mais FastAPI n’était pas installé. L’erreur était `ModuleNotFoundError: No module named 'fastapi'`.

Après `pip install -r requirements.txt`, génération des données et entraînement, les 23 tests s’exécutent.

## 2. Lancer Streamlit

**Lancez d’abord `streamlit run ui/app.py`. Que s’affiche-t-il dans le navigateur ?**

Dans cet environnement, `streamlit` n’est pas dans le `PATH` du terminal (l’exécutable n’existe que dans `.venv\Scripts`). La commande échoue donc, ou appellerait un autre Python s’il en existait un.

**Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?**

`python -m streamlit` lance le module Streamlit de l’interpréteur courant (ici `.venv`). `streamlit run` cherche un exécutable dans le `PATH`, qui peut manquer ou appartenir à un autre environnement. C’est la commande à retenir en TP3.

La page s’ouvre sur http://localhost:8501 :

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Elle affiche le titre « MaintAI · prédiction de panne », la barre latérale (URL de l’API, clé), et les onglets « Données » et « Prédiction ». L’onglet « Prédiction » contient les quatre champs du relevé et le bouton « Prédire ».

## 3. Sprint 1 : l’onglet « Données »

Code de l’onglet, dans `ui/app.py` :

```python
with onglet_donnees:
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

Avec `data/sensors.csv` (5 000 relevés synthétiques) :

| Indicateur | Valeur affichée |
|---|---:|
| Relevés | 5000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

**Choisissez `vibration_mm_s`. Comment évolue le taux de panne ? Laquelle des deux variables compte le plus ?**

Le taux de panne augmente nettement avec la vibration. En cinq tranches :

| Tranche de `vibration_mm_s` | Taux de panne |
|---|---:|
| (0,019 ; 1,26] | 1,3 % |
| (1,26 ; 2,08] | 2,3 % |
| (2,08 ; 3,0] | 5,7 % |
| (3,0 ; 4,48] | 12,9 % |
| (4,48 ; 22,23] | 45,8 % |

La vibration compte davantage que la température : le nuage le confirme, les pannes (points colorés) se concentrent surtout aux vibrations élevées. C’est cohérent avec `dataset.py`, où le coefficient de la vibration dans le risque est le plus fort.

**Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous, et qu’est-ce que cela montre ?**

À chaque interaction qui relance la page, Streamlit réexécute `ui/app.py` de la première à la dernière ligne. Le message `relance` réapparaît dans le terminal. Les curseurs du formulaire, eux, ne relancent rien tant qu’on n’appuie pas sur « Prédire » (`st.form`). Le `print` n’a pas été conservé dans le fichier rendu.

**À quoi sert `@st.cache_data` sur `charger` ?**

Sans lui, le CSV serait relu à chaque relance. Avec lui, le résultat est mis en cache pour le même chemin. Si le fichier change sans changer de chemin, il faut vider le cache Streamlit pour voir les nouvelles données.

À la fin du sprint 1, les tests de l’onglet « Données » passent. Il reste ceux de la prédiction.

## 4. Sprint 2 : l’onglet « Prédiction »

### Client HTTP — `maintai/client.py`

C’est le `fetch` du TP2, en Python. Les tests passent leur propre `http=` : il faut `self.http.post`, pas `httpx.post`.

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
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

### Dernière ligne de `python -m pytest` à la fin du sprint 2

```text
23 passed, 1 warning in 30.17s
```

Le warning vient de `fastapi.testclient` / `httpx` (`StarletteDeprecationWarning`). Les 23 tests sont verts.

| Fichier | Tests | Ce qu’ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | API FastAPI |
| `tests/test_client.py` | 3 | `MaintaiClient` (sans uvicorn) |
| `tests/test_data.py` | 3 | données |
| `tests/test_security.py` | 5 | clé API et CORS |
| `tests/test_train.py` | 3 | artefacts du modèle |
| `tests/test_ui.py` | 2 | page Streamlit (`AppTest`) |

### Essais dans Streamlit

L’API tourne sur le port **8001** (le 8000 peut déjà être pris), avec la clé de `.env` :

```powershell
python -m uvicorn maintai.api.main:app --reload --env-file .env --host 127.0.0.1 --port 8001
python -m streamlit run ui/app.py
```

Valeurs par défaut du formulaire : 72 °C, 6 mm/s, 85 %, 15 000 h. Le modèle répond `failure_probability = 0,9475`.

| Essai | Ce qu’affiche Streamlit |
|---|---|
| Valeurs par défaut, bonne clé (`test-key`) | Probabilité de panne **95 %** et `ALERTE : probabilité de panne 95% (seuil 30%)` |
| Valeurs par défaut, fausse clé | `Erreur 401 : Clé API absente ou invalide` |
| API arrêtée (Ctrl+C dans le terminal d’uvicorn) | `API injoignable : ...` |

Si l’API est lancée **sans** `.env` / `MAINTAI_API_KEY`, Streamlit affiche `Erreur 500 : MAINTAI_API_KEY n'est pas configurée sur le serveur`. La clé saisie dans la barre latérale voyage dans la requête ; le serveur doit aussi en avoir une pour la comparer.

### Pourquoi pas de CORS ?

Le port 8501 n’est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne.

En TP2, le JavaScript du navigateur envoyait `fetch` : CORS s’appliquait, et le port 5501 était bloqué. Ici, le navigateur parle à Streamlit (8501). C’est le **processus Python** de Streamlit qui appelle l’API avec `MaintaiClient` / `httpx`. Cette requête serveur-à-serveur n’est pas soumise à CORS. CORS protège l’utilisateur d’une page web tierce, pas un programme Python.

## 5. Questions de compréhension

1. **Dans la page web du TP2, qui envoie la requête à l’API ? Et dans Streamlit ?**

   TP2 : le JavaScript du navigateur, avec `fetch`.  
   TP3 : le serveur Streamlit, avec `MaintaiClient` (`self.http.post`).

2. **Pourquoi les tests de `test_client.py` n’ont-ils pas besoin d’uvicorn ?**

   La fixture crée un `fastapi.testclient.TestClient` et le passe à `MaintaiClient(..., http=client)`. L’appel reste dans le même processus, sans serveur réseau. `test_ui.py` va plus loin : `AppTest` exécute la page sans navigateur, et `monkeypatch` remplace `MaintaiClient.predict` par une réponse connue.

3. **Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle pour une démonstration à un client ? Et pour l’application d’un technicien ?**

   Pour une **démonstration** en une séance, avec métriques et graphiques : Streamlit. L’équipe code déjà en Python, et l’interface est prête sans JavaScript (ADR 004).  
   Pour une **application de technicien** intégrée à un produit, une page HTML/JS (ou une appli dédiée) donne plus de contrôle sur le design, l’auth et le déploiement. Streamlit reste un bon prototype.

## 6. Le rendu Git

- **Dépôt GitHub :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier de rendu :** `tp/tp3` ([dossier `tp`](https://github.com/yahyaLago/projet-deploiement-/tree/main/tp))
- **Branche principale :** `main`
- **Branche de travail :** `tp3`
- **Pull request :** à ouvrir après `git push -u origin tp3`, puis fusion et tag
- **Tag `tp3` :** à poser sur `main` après fusion (`git tag tp3` puis `git push --tags`)
- **Fichiers exclus :** `.env`, `data/*.csv`, `models/`, `.venv` (voir `.gitignore`)
- **ADR :** [`docs/adr/004-interface-streamlit.md`](docs/adr/004-interface-streamlit.md)

## 7. Ce qui reste flou

Rien de bloquant pour le TP3. Le point à retenir pour plus tard : Streamlit n’est pas bloqué par CORS parce que ce n’est pas le navigateur qui appelle l’API.
