# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membres :** Yahya Baid  ·  **Date :** 19/11/2026
heure:12:08
> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
32 passed, 4 warnings in 9.77s
```

Quels tests échouent, et pourquoi ?

Dans le starter, les cinq tests de `tests/test_tracking.py` échouaient parce que `log_run` n'était pas encore implémentée. Après son implémentation, les 32 tests passent. Les quatre avertissements actuels concernent les dépendances Starlette/HTTPX, SQLAlchemy et l'exemple d'entrée MLflow; ils ne font pas échouer les tests.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant, l'environnement du TP4 utilisait le package installé pour le TP4. Après `pip install -e .` exécuté depuis le dossier du TP5, le package doit pointer vers le dossier source TP5 en mode éditable. Le chemin exact avant l'installation n'a pas été relevé; pour le vérifier sur l'environnement utilisé, exécuter `python -m pip show maintai` et recopier `Location` et `Editable project location`.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 9.77s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande / run MLflow | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train --model forest` — `gentle-shrew-699` (`model=forest`, `threshold=0.3`) | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --threshold 0.2` — `hilarious-bear-847` (`model=logreg`, `C=1.0`, `threshold=0.2`) | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --C 0.01` — `painted-roo-545` (`model=logreg`, `C=0.01`, `threshold=0.3`) | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train` — `invincible-wasp-543` (`model=logreg`, `C=1.0`, `threshold=0.3`) | 0.750 | 0.622 | 0.904 |

Les quatre runs utilisent la version v1 des données (`data_md5=b7fec4274774842dc1f48202c6013490`) et `n_train=4000`.

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je choisirais provisoirement `hilarious-bear-847` (run_id `c83e9ea5946b4d258932046d6b7348e6`), car son recall de 0.838 est le plus élevé : il détecte le plus de pannes parmi ces quatre essais. Sa précision de 0.543 est la plus faible, donc ce choix implique davantage de fausses alertes. La décision finale devrait aussi tenir compte du coût acceptable des fausses alertes et être confirmée sur la v2.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

Le `requirements.txt` du modèle indique `scikit-learn==1.8.0`. Cela évite de dépendre d'une version implicite ou différente de scikit-learn lors du rechargement du modèle, problème de reproductibilité rencontré au TP4.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Les fichiers locaux `mlflow.db` et `mlruns/` contiennent les runs et leurs artefacts. Ils ne vont pas dans Git : ce sont des données générées localement, potentiellement volumineuses; le code et les résultats utiles sont suivis séparément.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

La commande `dvc add data/sensors.csv` a produit un fichier `data/sensors.csv.dvc` contenant la référence DVC. Pour la v1, l'empreinte relevée est :

```yaml
outs:
- md5: b7fec4274774842dc1f48202c6013490
  hash: md5
  path: sensors.csv
```

Le fichier `.dvc` complet peut aussi contenir la taille exacte; elle n'a pas été relevée dans la sortie du terminal conservée ici.

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

La v1 a le MD5 `b7fec4274774842dc1f48202c6013490`, identique au paramètre `data_md5` des quatre runs MLflow affichés. Cela relie ces entraînements à la v1. La v2 a une empreinte différente (`31ef5ebb63ef2331a31dfe009ef8796a`).

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

`data/sensors.csv` est le fichier de données lui-même, que Git ne gère pas efficacement avec plusieurs versions. DVC stocke son contenu dans le cache/stockage et Git suit le petit fichier `data/sensors.csv.dvc`, qui indique notamment l'empreinte nécessaire pour retrouver cette version.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data/sensors.csv.dvc:
        changed outs:
                modified:           data/sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `4c38112` | `b7fec427` | 5 000 relevés (5 001 lignes avec l'en-tête) |
| v2 | `4296b75` | `31ef5ebb` | 8 000 relevés (8 001 lignes avec l'en-tête) |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Le retour à la v1 avec `git checkout 4c38112 -- tp/tp5/data/sensors.csv.dvc` puis `dvc checkout` a restauré 5 000 relevés (5 001 lignes avec l'en-tête). Le retour à la v2 avec le commit `4296b75` a restauré 8 000 relevés (8 001 lignes avec l'en-tête).

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

Après suppression du CSV et du cache DVC local, `dvc pull` a récupéré le fichier depuis le stockage : `1 file fetched and 1 file added`. Le CSV restauré contenait 8 001 lignes (8 000 relevés et l'en-tête).

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | `b7fec427` | 4 000 | 0.838 (`hilarious-bear-847`) | 0.543 |
| v2 | `31ef5ebb` | 6 400 | 0.824 (`fun-dove-613`) | 0.567 |

Les deux runs utilisent la régression logistique, `C=1.0` et `threshold=0.2`. Sur la v1, le recall est supérieur de 0.014; sur la v2, la précision est supérieure de 0.024 et l'accuracy de 0.015 (0.897 contre 0.882). Le run v2 utilise 6 400 exemples d'entraînement, contre 4 000 pour v1. Le run v2 est `fun-dove-613` (`run_id=6f2ba3ea99e24c2bb9c6e18ba15d6a4a`, `data_md5=31ef5ebb63ef2331a31dfe009ef8796a`).

On ne peut pas conclure simplement que le modèle v2 est « meilleur » : les données et le nombre d'exemples changent, donc les ensembles d'entraînement et de test aussi. Le rappel baisse légèrement sur v2 alors que précision et exactitude progressent. Comme une panne manquée coûte plus cher, la v1 garde le meilleur recall observé; il faut néanmoins valider le choix sur des données de test représentatives avant le déploiement.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md` : la décision compare maintenant les runs v1 et v2 avec les mêmes réglages.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   Git versionne le code et les fichiers de suivi; DVC versionne les données volumineuses en gardant leurs références dans Git et leur contenu dans un stockage; MLflow garde les paramètres, métriques, versions de données et modèles de chaque entraînement.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le chemin `~/dvc-stockage` est propre à cette machine et ne doit pas être partagé dans Git, d'où `--local`. Pour le partager en groupe, il faudrait configurer un stockage accessible à tous (serveur ou stockage cloud) et donner à chaque membre l'accès et la configuration nécessaires.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le modèle entraîné (`models/model.joblib` localement et artefact `model` dans MLflow), son contrat d'entrée/prétraitement (`models/model_info.json` et le pipeline enregistré) et l'environnement logiciel (versions des dépendances dans `requirements.txt`, également enregistré avec le modèle MLflow).

## 7. Le rendu Git

- Lien de la pull request : à créer depuis la branche `tp5-yahya-baid` vers `main` (dépôt https://github.com/yahyaLago/projet-deploiement-).
- Le tag `tp5` existe sur GitHub : non (tags actuels : `tp1`, `tp2`, `tp3` ; le tag `tp4` n'est pas encore présent).
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` n'apparaissent pas. Ils sont ignorés par Git. Les fichiers de suivi DVC (`.dvc`, `.dvcignore`, `data/sensors.csv.dvc`) sont versionnés. La branche locale `tp5-yahya-baid` est prête ; le push et la pull request attendent confirmation.

## 8. Ce qui reste flou

Point de vigilance restant : confirmer les métriques sur des données de test représentatives avant de déployer, car le changement de version des données modifie les échantillons d'entraînement et de test.
## 9. Grid Search

Les réglages ont été comparés manuellement avec quatre runs MLflow sur la v1, plutôt qu'avec un `GridSearchCV` automatique. Le rappel est le critère prioritaire, car une panne manquée coûte plus cher qu'une fausse alerte.

| Modèle | C | Seuil | Recall | Précision | Accuracy |
|---|---:|---:|---:|---:|---:|
| Forêt aléatoire | — | 0.3 | 0.728 | 0.562 | 0.886 |
| Régression logistique | 1.0 | 0.2 | **0.838** | 0.543 | 0.882 |
| Régression logistique | 0.01 | 0.3 | 0.691 | **0.653** | **0.908** |
| Régression logistique | 1.0 | 0.3 | 0.750 | 0.622 | 0.904 |

Parmi les essais, le meilleur rappel est obtenu par la régression logistique avec `C=1.0` et un seuil de `0.2` (run `hilarious-bear-847`). Ce réglage est retenu provisoirement pour limiter les pannes manquées, malgré une précision plus faible et donc davantage de fausses alertes. La comparaison v1/v2 avec ce même réglage donne un recall de 0.838 sur v1 et de 0.824 sur v2; elle ne remplace pas une validation sur des données de test représentatives.