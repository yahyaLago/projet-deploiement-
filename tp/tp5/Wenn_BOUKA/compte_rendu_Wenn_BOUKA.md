# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membre :** Wenn BOUKA  ·  **Date :** 20/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp5/Wenn_BOUKA`  
**Fichiers rendus :** `maintai/tracking.py`, `maintai/train.py`, `docs/adr/004-choix-du-modele.md`, ce compte rendu

---

## 1. Mise en place (dans `TP/TP5`)

```bash
pip install -r requirements.txt
pip install -e .
python -m maintai.dataset
python -m pytest
```

**Quels tests échouent, et pourquoi ?**

Au départ, ce sont les tests de `tests/test_tracking.py` : `log_run` n'est pas encore écrite, donc aucun run n'est enregistré et rien ne peut être relu dans MLflow. Les tests hérités du TP4 (API, client, CLI, package, interface) passent. Une fois `log_run` écrite, tout le projet est vert ; j'ai aussi vérifié séparément que le run enregistré contient bien `data_md5`, les paramètres, les métriques, et que le modèle se recharge avec `mlflow.sklearn.load_model("runs:/<id>/model")`.

**Avant `pip install -e .`, où pointait le package `maintai` installé ? Et après ?**

Avant, l'environnement gardait l'installation éditable du TP4 : `pip show maintai` donnait `Editable project location: …/TP4`. `import maintai` aurait donc chargé l'ancien `train.py`, sans MLflow. Après `pip install -e .` lancé dans le dossier du TP5 :

```text
Name: maintai
Version: 0.2.0
Location: …/.venv/lib/site-packages
Editable project location: …/TP5
```

Une installation éditable pointe vers **un seul dossier** : changer de TP impose de réinstaller, sinon on teste le code d'un autre TP sans s'en rendre compte.

## 2. Sprint 1 : MLflow

Ma fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        # 1. les réglages, plus l'empreinte des données : c'est elle qui relie le run à une version DVC
        mlflow.log_params({**params, "data_md5": file_md5(data_path)})
        # 2. les résultats, pour comparer les runs dans mlflow ui
        mlflow.log_metrics(metrics)
        # 3. le modèle lui-même, avec un exemple d'entrée (signature) et son requirements.txt
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
    return run.info.run_id
```

`with mlflow.start_run()` ferme le run même si une étape plante : le run est marqué `FAILED` au lieu de rester ouvert. `data_md5` est rangé avec les paramètres parce que c'est une **entrée** de l'entraînement, au même titre que `C` ou le seuil.

**Mes runs sur la v1** (5 000 relevés, `n_train = 4000`, `data_md5 = b7fec427…`), relevés dans `mlflow ui` :

| Commande | Run MLflow | recall | precision | accuracy |
|---|---|---:|---:|---:|
| `python -m maintai.train` (logreg, `C=1`, seuil 0,3) | `sneaky-horse-146` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --threshold 0.2` | `valuable-rat-309` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --C 0.01` | `victorious-hare-456` | 0.691 | 0.653 | **0.908** |
| `python -m maintai.train --model forest` | `indecisive-mare-42` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --threshold 0.15` | `grandiose-bee-356` | **0.875** | 0.500 | 0.864 |
| `python -m maintai.train --model forest --threshold 0.2` | `beautiful-sloth-685` | 0.831 | 0.479 | 0.854 |

Pour situer ces chiffres, la baseline (toujours prédire « pas de panne ») atteint **0.864** d'accuracy… avec un recall de **0** : elle ne détecte aucune panne. L'accuracy seule est donc trompeuse sur un jeu où 13,6 % des relevés sont des pannes.

**Quel run choisiriez-vous pour MaintAI, et pourquoi ?**

`grandiose-bee-356` (`run_id = cf595aee40fa4219817e00b676dcab3c`) : régression logistique, `C=1`, **seuil 0,15**. C'est le meilleur recall mesuré (0.875) : sur 8 pannes réelles, il en détecte 7, contre 6 avec le seuil 0,3. En échange, la précision tombe à 0.500, soit une fausse alerte pour une vraie. Comme une panne manquée coûte plus cher qu'une inspection inutile, j'accepte ce compromis.

Deux constats appuient ce choix :
- Le **seuil** a plus d'effet que le modèle ou la régularisation. Passer de 0,3 à 0,15 fait gagner 12,5 points de recall, alors que la forêt aléatoire fait moins bien que la régression logistique au même seuil (0.728 contre 0.750 à 0,3, et 0.831 contre 0.838 à 0,2).
- Le run `C=0.01` a la meilleure accuracy mais le plus mauvais recall : optimiser l'accuracy aurait choisi le pire modèle pour notre besoin.

**Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?**

L'artefact `model/` du run contient `MLmodel`, `model.skops`, `input_example.json`, `conda.yaml`, `python_env.yaml` et un `requirements.txt` :

```text
mlflow==3.18.0
numpy==2.4.4
pandas==3.0.2
scikit-learn==1.8.0
scipy==1.18.1
skops==0.16.0
…
```

`scikit-learn==1.8.0` y est figé. Au TP4, le wheel déclarait `scikit-learn>=1.4`, pip installait la 1.9.1 et le modèle se chargeait avec un `InconsistentVersionWarning`. Ici, la version exacte voyage **avec** le modèle : on sait toujours dans quel environnement le recharger.

**Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?**

Dans le dossier où l'on lance l'entraînement : `mlflow.db` (base SQLite : runs, paramètres, métriques ; environ 1 Mo après 8 runs) et `mlruns/` (les artefacts, dont les modèles). Ils ne vont pas dans Git : ce sont des **résultats** générés, régénérables en relançant l'entraînement, binaires et qui grossissent à chaque run. Ils sont listés dans `.gitignore`. Git garde le code qui les produit.

## 3. Sprint 2 : DVC

```bash
dvc init
dvc remote add -d --local stockage ~/dvc-stockage
dvc add data/sensors.csv
git add data/sensors.csv.dvc .dvc .dvcignore
git commit -m "Donnees v1 (5000 releves)"
dvc push
```

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```yaml
outs:
- md5: b7fec4274774842dc1f48202c6013490
  size: 121814
  hash: md5
  path: sensors.csv
```

**Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?**

Ce sont exactement les mêmes : `b7fec4274774842dc1f48202c6013490`. `file_md5` calcule l'empreinte du fichier comme DVC. Un run MLflow désigne donc sans ambiguïté la version des données qui l'a produit, et le fichier `.dvc` permet de la retrouver.

**Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?**

Le CSV est **le contenu** : gros, il change à chaque nouvelle collecte, et Git en garderait une copie complète par version, pour toujours. Le `.dvc` est **une étiquette** de quelques lignes (empreinte, taille, nom) : Git la versionne comme du code. Le contenu lui-même est rangé dans le cache et le stockage DVC, retrouvé grâce à l'empreinte.

**Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?**

```text
8000 relevés écrits dans data/sensors.csv (taux de panne : 12.8%)

data/sensors.csv.dvc:
	changed outs:
		modified:           data/sensors.csv
```

DVC voit que le fichier ne correspond plus à l'empreinte enregistrée. J'ai ensuite fait `dvc add`, un commit et un `dvc push` pour la v2 :

```yaml
outs:
- md5: 31ef5ebb63ef2331a31dfe009ef8796a
  size: 194833
  hash: md5
  path: sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `ff18bfc Donnees v1 (5000 releves)` | `b7fec427` | 5 001 (5 000 relevés + en-tête) |
| v2 | `2dca379 Donnees v2 (8000 releves)` | `31ef5ebb` | 8 001 (8 000 relevés + en-tête) |

**Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.**

```text
$ git checkout ff18bfc -- data/sensors.csv.dvc
$ dvc checkout
M       data/sensors.csv
$ wc -l data/sensors.csv           # Windows : (Get-Content data\sensors.csv).Count
5001 data/sensors.csv

$ git checkout 2dca379 -- data/sensors.csv.dvc
$ dvc checkout
M       data/sensors.csv
$ wc -l data/sensors.csv
8001 data/sensors.csv
```

Git ramène l'étiquette, `dvc checkout` remplace le fichier par le contenu qui lui correspond, pris dans le cache. On voyage entre les versions des données comme entre des versions du code.

**Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?**

```text
$ dvc pull
A       data/sensors.csv
1 file fetched and 1 file added

$ wc -l data/sensors.csv
8001 data/sensors.csv
$ dvc status
Data and pipelines are up to date.
```

Le cache local a disparu, mais une copie existe dans le stockage DVC (alimenté par `dvc push`). `dvc pull` la retélécharge dans le cache puis la remet en place : c'est ce que ferait un collègue qui clone le dépôt.

## 4. Relier modèle et données

Même réglage que mon choix (logreg, `C=1`, seuil 0,15), entraîné sur chaque version. J'ai fait la même comparaison au seuil 0,2 pour vérifier que la tendance tient.

| Run | data_md5 (8 caractères) | n_train | seuil | recall | precision | accuracy |
|---|---|---:|---:|---:|---:|---:|
| v1 · `grandiose-bee-356` | `b7fec427` | 4 000 | 0,15 | **0.875** | 0.500 | 0.864 |
| v2 · `polite-horse-748` | `31ef5ebb` | 6 400 | 0,15 | 0.859 | **0.506** | **0.874** |
| v1 · `valuable-rat-309` | `b7fec427` | 4 000 | 0,2 | 0.838 | 0.543 | 0.882 |
| v2 · `spiffy-snipe-93` | `31ef5ebb` | 6 400 | 0,2 | 0.824 | 0.567 | 0.897 |

Aux deux seuils, la v2 donne un recall légèrement plus bas (‑1,6 point à 0,15) et une précision et une accuracy légèrement plus hautes. Je ne conclus pas pour autant que le modèle v2 est meilleur ou moins bon :
- le **jeu de test n'est pas le même** (1 000 relevés pour la v1, 1 600 pour la v2) : on compare deux examens différents ;
- la v2 est générée avec une autre graine et a un taux de panne plus faible (12,8 % contre 13,6 %), ce qui change mécaniquement précision et recall ;
- les écarts représentent 2 à 3 pannes, sur des tests qui en contiennent 136 (v1) et 205 (v2).

Pour trancher, il faudrait évaluer les deux modèles **sur un même jeu de test fixé**, et non sur le découpage propre à chaque version. C'est précisément ce que la traçabilité permet : grâce à `data_md5`, je sais exactement sur quelles données chaque chiffre a été obtenu.

## 5. Décision : l'ADR 004

Voir [`docs/adr/004-choix-du-modele.md`](docs/adr/004-choix-du-modele.md) : régression logistique, `C=1`, seuil 0,15, run de référence `grandiose-bee-356` sur la v1.

## 6. Questions de compréhension

**1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?**  
Git versionne le **code** et les petits fichiers texte, dont les étiquettes `.dvc`. DVC versionne les **données** : leur contenu est dans un cache et un stockage à part, Git ne garde que l'empreinte. MLflow garde l'**histoire des entraînements** : pour chaque run, les réglages, la version des données (`data_md5`), les métriques et le modèle avec son environnement. Ensemble, ils répondent à « quel code, sur quelles données, a produit ce modèle, avec quels résultats ? ».

**2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?**  
`--local` écrit la configuration dans `.dvc/config.local`, qui n'est pas commité : le chemin `~/dvc-stockage` n'existe que sur ma machine, et le commiter casserait `dvc pull` chez les autres. Pour partager, il faut un stockage que tous peuvent atteindre (dossier réseau, S3, Google Drive, serveur SSH), déclaré sans `--local` dans `.dvc/config`, donc commité. Chacun garde ses identifiants d'accès dans son propre `config.local`. Après `git pull`, un `dvc pull` suffit alors à récupérer exactement les mêmes données.

**3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?**  
- **Le modèle entraîné** : `models/model.joblib` en local, et l'artefact `model/` (`model.skops`) de chaque run MLflow.
- **Son contrat d'entrée** (colonnes, seuil, prétraitement) : `models/model_info.json`, le pipeline qui inclut le scaler, et la signature et `input_example.json` enregistrés par MLflow.
- **Son environnement** : `requirements.txt` du projet, et désormais le `requirements.txt` / `conda.yaml` livrés *avec* le modèle par MLflow.

S'y ajoute maintenant la **version des données**, via `data_md5` dans le run et le fichier `.dvc` dans Git.

## 7. Le rendu Git

- **Mon dossier :** `tp/tp5/Wenn_BOUKA/`, avec `maintai/tracking.py`, `maintai/train.py`, `docs/adr/004-choix-du-modele.md` et ce compte rendu
- **Branche :** `tp-wenn-bouka`, pull request vers `main`
- **`git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ?** Non. `git status --ignored` les classe en `!!` (ignorés), comme `.dvc/config.local`. Les fichiers de suivi `data/sensors.csv.dvc`, `.dvc/config` et `.dvcignore` sont, eux, versionnés.

## 8. Ce qui reste flou

- **Comparer v1 et v2 honnêtement.** Chaque version a son propre jeu de test ; je ne sais pas encore comment organiser un jeu de test figé, versionné à part avec DVC, sur lequel évaluer tous les modèles.
- **Choisir le seuil sans regarder le test.** J'ai réglé le seuil en lisant le recall sur le jeu de test, ce qui l'optimise sur ces mêmes données. Il faudrait un jeu de validation séparé (ou une validation croisée) pour le choisir, puis garder le test pour la mesure finale.
