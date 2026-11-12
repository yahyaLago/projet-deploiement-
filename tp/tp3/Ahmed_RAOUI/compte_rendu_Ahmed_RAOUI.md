# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Auteur :** Ahmed RAOUI  
**Email :** ahmedraoui1818@gmail.com  
**Groupe :** G1My  
**Date :** 12/11/2026

---

## 1. Mise en place (dans `TP/TP3`)

Le starter du TP3 reprend l’API du TP2 et ajoute `maintai/client.py`, `ui/app.py`, `tests/test_client.py` et `tests/test_ui.py`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
python -m pytest -v
```

Lors du premier lancement de `python -m pytest -v`, après installation des dépendances et avant de compléter les sprints, j'ai obtenu :

```text
5 failed, 18 passed, 1 warning in 36.36s
```

**Quels fichiers de tests échouent, et quelle erreur donnent-ils ?**

- `tests/test_client.py` : trois tests échouaient avec `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`, car la méthode de prédiction n'était pas implémentée.
- `tests/test_ui.py` : deux tests échouaient avec `IndexError: list index out of range`, car les éléments demandés dans l'interface Streamlit n'étaient pas encore tous présents.

Après avoir complété les deux sprints, j'ai obtenu **23 tests réussis**.

## 2. Lancer Streamlit

**Lancez d’abord `streamlit run ui/app.py`. Que s’affiche-t-il dans le navigateur ?**

Je n'ai pas vérifié cette commande séparément. J'ai utilisé `python -m streamlit run ui/app.py` pour lancer l'application depuis l'environnement virtuel.

**Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?**

`python -m streamlit` lance Streamlit avec l'interpréteur Python actif, ici celui de `.venv`. La commande `streamlit run` dépend de la présence de l'exécutable `streamlit` dans le `PATH` ; lorsqu'il est disponible dans l'environnement actif, elle peut également fonctionner.

La page s'ouvre à l'adresse http://localhost:8501 :

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Elle affiche le titre « MaintAI · prédiction de panne », la barre latérale (URL de l'API et clé), ainsi que les onglets « Données » et « Prédiction ». L'onglet « Prédiction » contient quatre champs de relevé et le bouton « Prédire ».

Au premier démarrage, le fichier `data/sensors.csv` était absent (`FileNotFoundError`). J'ai exécuté `python -m maintai.dataset`, qui a généré 5 000 relevés avec un taux de panne de 13,6 %, puis relancé Streamlit.

## 3. Sprint 1 : l’onglet « Données »

Code ajouté dans `ui/app.py` (en conservant les commentaires du starter) :

```python
col1, col2, col3 = st.columns(3)

col1.metric("Nombre de relevés", len(df))
col2.metric("Taux de panne", f"{df.failure.mean() * 100:.1f} %")
col3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

variable = st.selectbox("Choisir une variable", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux_panne = df.groupby(tranches, observed=True)["failure"].mean() * 100
taux_panne.index = taux_panne.index.astype(str)
st.bar_chart(taux_panne)

st.scatter_chart(
    df,
    x="temperature_c",
    y="vibration_mm_s",
    color="failure"
)
```

Avec `data/sensors.csv` (5 000 relevés synthétiques) :

| Indicateur | Valeur affichée |
|---|---:|
| Relevés | 5 000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

**Choisissez `vibration_mm_s`. Comment évolue le taux de panne ? Laquelle des deux variables compte le plus ?**

Le graphique permet d'analyser le taux de panne en fonction des tranches de vibration. D'après le mécanisme de génération du jeu de données et l'analyse attendue, les vibrations élevées sont associées à davantage de pannes ; la vibration joue un rôle important dans le risque. Dans mon implémentation, j'ai utilisé `pd.cut(..., bins=10)` : les valeurs des tranches sont donc différentes de celles obtenues avec `pd.qcut(..., q=5)`. Je n'ai pas relevé les pourcentages précis après sélection de `vibration_mm_s` et n'en indique donc pas ici.

**Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous, et qu’est-ce que cela montre ?**

Streamlit réexécute le script à chaque interaction qui déclenche une relance. Un `print("relance")` placé en haut du fichier permet de l'observer dans le terminal. Dans un formulaire `st.form`, les modifications des curseurs sont soumises ensemble lors du clic sur « Prédire ». Je n'ai pas effectué ce test avec `print` pendant ma réalisation ; il reste à vérifier directement si demandé.

**À quoi sert `@st.cache_data` sur `charger` ?**

`@st.cache_data` met en cache le DataFrame chargé pour éviter de relire inutilement le fichier CSV lors des relances du script. Le cache peut être invalidé lorsque les données ou les paramètres pertinents changent, et il peut aussi être vidé manuellement.

À la fin du sprint 1, les indicateurs et graphiques de l'onglet « Données » s'affichaient correctement.

## 4. Sprint 2 : l’onglet « Prédiction »

### Client HTTP — `maintai/client.py`

C’est l'équivalent du `fetch` du TP2, en Python. Les tests passent leur propre `http=` : il faut appeler `self.http.post`, et non `httpx.post` directement.

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {}

    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post(
        "/v1/predict",
        json=reading,
        headers=headers
    )

    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))

    return r.json()
```

Dans `ui/app.py`, lors de l'envoi du formulaire, je crée `MaintaiClient`, j'appelle `predict(releve)` et j'affiche la probabilité de panne. Les erreurs de type `APIError` sont affichées avec `st.warning`, et celles de type `httpx.HTTPError` avec `st.error`. Si la prédiction est réussie, l'interface affiche une alerte rouge ou un message de fonctionnement normal.

### Dernière ligne de `python -m pytest` à la fin du sprint 2

```text
23 passed, 1 warning in 10.27s
```

L'avertissement provient de l'utilisation de `httpx` avec `starlette.testclient` (`StarletteDeprecationWarning`). Il ne fait échouer aucun test.

| Fichier | Tests | Ce qu’ils vérifient |
|---|---:|---|
| `tests/test_api.py` | 7 | API FastAPI |
| `tests/test_client.py` | 3 | `MaintaiClient` sans uvicorn |
| `tests/test_data.py` | 3 | Données |
| `tests/test_security.py` | 5 | Clé API et CORS |
| `tests/test_train.py` | 3 | Artefacts du modèle |
| `tests/test_ui.py` | 2 | Interface Streamlit (`AppTest`) |

### Essais dans Streamlit

L'API a été démarrée sur le port **8000** avec les variables du fichier `.env` :

```powershell
python -m uvicorn maintai.api.main:app --reload --env-file .env
python -m streamlit run ui/app.py
```

Pendant la mise en place, j'ai rencontré les erreurs suivantes :

- `500` : variable `MAINTAI_API_KEY` non configurée côté serveur. Résolution : créer `.env` et lancer uvicorn avec `--env-file .env`.
- `401` : clé API absente ou incorrecte dans la requête. Résolution : renseigner `x-api-key` dans Swagger, puis la clé dans la barre latérale de Streamlit.
- `503` : modèle non chargé. Résolution : lancer `python -m maintai.train`, ce qui a créé `models/model.joblib`, puis redémarrer l'API.

| Essai | Résultat observé |
|---|---|
| Swagger, bonne clé et modèle entraîné | `200 OK`, `failure_probability = 0.9553`, `alert = true`, `threshold = 0.3` |
| Streamlit, valeurs par défaut et bonne clé | Probabilité affichée : **95 %** ; message « ALERTE : risque de panne détecté ! » |
| Swagger, requête sans clé valide | `401` : « Clé API absente ou invalide » |
| Swagger, avant entraînement du modèle | `503` : modèle non chargé |

### Pourquoi pas de CORS ?

Le port 8501 n'est pas nécessairement autorisé dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne.

En TP2, le JavaScript du navigateur utilisait `fetch` directement vers l'API : les règles CORS s'appliquaient. Dans le TP3, le navigateur communique avec Streamlit ; c'est le processus Python de Streamlit qui appelle FastAPI avec `MaintaiClient` et `httpx`. Les restrictions CORS des navigateurs ne s'appliquent pas aux requêtes Python serveur-à-serveur.

## 5. Questions de compréhension

1. **Dans la page web du TP2, qui envoie la requête à l’API ? Et dans Streamlit ?**

   TP2 : le JavaScript exécuté par le navigateur, avec `fetch`.  
   TP3 : le serveur Streamlit, avec `MaintaiClient` et `self.http.post`.

2. **Pourquoi les tests de `test_client.py` n’ont-ils pas besoin d’uvicorn ?**

   Les tests utilisent `fastapi.testclient.TestClient`, transmis à `MaintaiClient(..., http=client)`. Les requêtes sont traitées localement, sans démarrer de serveur réseau. Les tests de l'interface peuvent utiliser `AppTest` pour exécuter Streamlit sans navigateur.

3. **Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle pour une démonstration à un client ? Et pour l’application d’un technicien ?**

   Pour une **démonstration**, je choisirais Streamlit : il permet de créer rapidement un tableau de bord avec métriques, graphiques et prédictions en Python. Pour une **application destinée aux techniciens**, une interface HTML/JavaScript ou une application dédiée permettrait davantage de personnalisation, d'intégration et de contrôle sur l'expérience utilisateur. Streamlit convient bien au prototypage.

## 6. Le rendu Git

- **Dépôt GitHub :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier de rendu :** `tp/tp3`
- **Branche principale :** `main`
- **Compte rendu individuel :** `tp/tp3/compte_rendu_Ahmed_RAOUI.md`
- **État du dépôt local :** dépôt commun cloné ; compte rendu individuel créé, mais pas encore envoyé sur GitHub au moment de la rédaction
- **Pull request et tag `tp3` :** à coordonner avec le groupe, sans écraser les contributions existantes
- **Fichiers à exclure :** `.env`, `.venv`, fichiers de données générés et artefacts du modèle, selon `.gitignore`
- **ADR :** [`docs/adr/004-interface-streamlit.md`](docs/adr/004-interface-streamlit.md)

## 7. Ce qui reste flou

Les principaux problèmes techniques rencontrés (chargement des données, clé API, modèle non entraîné) ont été résolus. Le point à retenir est la différence entre une requête du navigateur soumise à CORS et une requête Python serveur-à-serveur. Il reste à finaliser le dépôt Git du compte rendu individuel et à coordonner les contributions avec le groupe.
