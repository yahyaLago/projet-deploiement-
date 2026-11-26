# TP5 — Suivre les entraînements et versionner les données

**Auteur :** Mazine CHATER  
**Email :** mazine4pro@gmail.com  
**Groupe :** G1 5IADATA Moulay Youssef  
**Date :** 19/11/2026  
**Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-), dossier `tp/tp5`

---

## 1. Mise en place

Le TP5 reprend MaintAI au point où le TP4 l'a laissé. J'ouvre un environnement propre dans `tp/tp5` pour ne pas réutiliser par erreur les dépendances du TP4.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

Au premier passage, cinq tests échouent :

```text
5 failed, 27 passed
```

Les cinq échecs sont dans `tests/test_tracking.py`. Ils vérifient qu'un entraînement crée un run MLflow, que les métriques et l'empreinte des données y sont enregistrées, que le modèle est stocké et que les options `--model` et `--threshold` changent le run. Tant que `log_run` n'est pas implémentée, aucun run n'existe : les tests ne trouvent rien à contrôler. Les 27 autres tests passent, car ils ne dépendent pas de MLflow.

Après l'implémentation, j'obtiens :

```text
32 passed, 4 warnings in 9.77s
```

Les quatre avertissements viennent de dépendances (Starlette/HTTPX, SQLAlchemy et un exemple d'entrée MLflow). Aucun ne fait échouer un test. Les 32 tests se répartissent entre l'API (7), le client (3), les données (3), la sécurité (5), l'entraînement (3), le packaging (2), le suivi MLflow (5), l'interface (2) et la CLI (2).

**Où pointe le package `maintai` ?** Avant `pip install -e .`, l'environnement peut encore résoudre `maintai` vers l'installation du TP4. Après la commande lancée depuis `tp/tp5`, le package est lié au dossier source du TP5 :

```powershell
python -c "import maintai; print(maintai.__file__)"
# ...\tp\tp5\maintai\__init__.py
pip show maintai
# Editable project location: ...\tp\tp5
```

C'est le même mécanisme qu'au TP4 : pip ne copie pas le code, il crée un lien. Sans cette installation, les tests pourraient importer le code du TP4 et les résultats seraient faux.

## 2. Sprint 1 : MLflow

La fonction `log_run` de `maintai/tracking.py` :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
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

Chaque run contient les paramètres (`model`, `C`, `threshold`, `n_train`), l'empreinte `data_md5`, les métriques et le modèle sérialisé. `input_example` documente la forme de l'entrée attendue. `skops_trusted_types` est nécessaire pour recharger la forêt aléatoire, dont les arbres ne font pas partie des types autorisés par défaut. La fonction renvoie `run_id`, ce qui permet de le citer dans le terminal et dans l'ADR.

`file_md5` lit le fichier par blocs d'un mégaoctet. Sur un gros CSV, lire tout le fichier d'un coup consommerait inutilement de la mémoire ; le résultat reste le même MD5 que celui calculé par DVC.

Les quatre runs de la v1 :

| Commande | Run MLflow | Paramètres | Recall | Precision | Accuracy |
|---|---|---|---:|---:|---:|
| `python -m maintai.train` | `invincible-wasp-543` | logreg, `C=1.0`, seuil 0.3 | 0.750 | 0.622 | 0.904 |
| `... --threshold 0.2` | `hilarious-bear-847` | logreg, `C=1.0`, seuil 0.2 | 0.838 | 0.543 | 0.882 |
| `... --C 0.01` | `painted-roo-545` | logreg, `C=0.01`, seuil 0.3 | 0.691 | 0.653 | 0.908 |
| `... --model forest` | `gentle-shrew-699` | forêt, seuil 0.3 | 0.728 | 0.562 | 0.886 |

Les quatre runs utilisent la v1 (`data_md5=b7fec427...`) et 4 000 exemples d'entraînement. Le seuil est un paramètre du run, pas seulement une valeur de l'API : c'est lui qui transforme la probabilité en alerte.

**Quel run choisir ?** Je retiens `hilarious-bear-847` (seuil 0.2), car il a le meilleur recall (0.838). Dans ce projet, une panne manquée coûte plus cher qu'une fausse alerte. En contrepartie, sa précision est la plus faible (0.543), donc il déclenchera plus d'alertes inutiles. Ce choix reste provisoire : il doit être confirmé sur la v2 et sur un jeu de test représentatif. La forêt aléatoire, comparée sur les mêmes données, ne fait pas mieux en recall (0.728) et n'apporte pas d'avantage assez net pour justifier sa complexité.

**Version de scikit-learn.** Le `requirements.txt` du modèle MLflow indique `scikit-learn==1.8.0`. C'est la version qui a écrit `model.joblib`. Au TP4, un environnement neuf avait installé une version plus récente et le chargement affichait `InconsistentVersionWarning`. En enregistrant la version exacte avec le modèle, MLflow permet de reconstruire un environnement compatible et règle ce problème de reproductibilité.

**Où MLflow stocke-t-il les runs ?** En local, MLflow utilise `mlflow.db` (base SQLite) et le dossier `mlruns/` pour les artefacts. Ces fichiers ne vont pas dans Git : ils sont générés par les entraînements, peuvent devenir volumineux et contiennent des artefacts binaires. Ils sont propres à ma machine. Pour un travail d'équipe, il faudrait un serveur de tracking ou un stockage distant partagé.

## 3. Sprint 2 : DVC

```powershell
dvc init --subdir
dvc add data/sensors.csv
dvc remote add --local -d stockage C:/dvc-stockage
dvc push
```

`dvc init --subdir` crée la configuration DVC dans `tp/tp5` et non à la racine du dépôt. Chaque TP garde ainsi ses propres données et son propre cache, sans mélanger les versions des autres dossiers.

Le fichier `data/sensors.csv.dvc` de la v1 :

```yaml
outs:
- md5: b7fec4274774842dc1f48202c6013490
  hash: md5
  path: sensors.csv
```

Le MD5 est identique au paramètre `data_md5` des quatre runs de la v1. C'est le lien entre un entraînement MLflow et la version exacte des données : si le CSV change, le MD5 change et le run ne peut plus être confondu avec un autre.

**Pourquoi le CSV n'est-il pas dans Git ?** Le fichier de données est volumineux, binaire du point de vue de Git et remplacé en entier à chaque régénération. Le versionner ferait grossir l'historique à chaque essai. DVC stocke le contenu dans son cache et dans le remote, et Git ne suit que le petit fichier `.dvc`, lisible et comparable d'une version à l'autre.

Après `python -m maintai.dataset --n 8000 --seed 7`, `dvc status` signale que le fichier a changé :

```text
data/sensors.csv.dvc:
        changed outs:
                modified:           data/sensors.csv
```

Je crée alors la v2 avec `dvc add data/sensors.csv`, puis je commit le nouveau `.dvc`.

| Version | Commit Git | MD5 (8 caractères) | Nombre de lignes |
|---|---|---|---:|
| v1 | `4c38112` | `b7fec427` | 5 001 (5 000 relevés + en-tête) |
| v2 | `4296b75` | `31ef5ebb` | 8 001 (8 000 relevés + en-tête) |

Pour revenir à la v1 :

```powershell
git checkout 4c38112 -- tp/tp5/data/sensors.csv.dvc
dvc checkout
```

`dvc checkout` restaure le fichier depuis le cache DVC. Le CSV contient de nouveau 5 001 lignes. En checkoutant le `.dvc` de la v2 et en relançant `dvc checkout`, je retrouve 8 001 lignes. Je n'ai pas régénéré les données : j'ai restauré exactement les octets de chaque version.

Enfin, je supprime `data/sensors.csv` et le dossier `.dvc/cache`, puis je lance `dvc pull` :

```text
1 file fetched and 1 file added
```

Le fichier est récupéré depuis le remote, pas depuis le cache local. C'est la preuve que le stockage distant est la source de vérité et qu'un autre membre du groupe pourrait récupérer les données sans les régénérer.

## 4. Relier modèle et données

J'entraîne un modèle sur la v2 avec les mêmes réglages que le run retenu :

```powershell
python -m maintai.train --threshold 0.2
```

| Version | Run | data_md5 (8) | n_train | Recall | Precision |
|---|---|---|---:|---:|---:|
| v1 | `hilarious-bear-847` | `b7fec427` | 4 000 | 0.838 | 0.543 |
| v2 | `fun-dove-613` | `31ef5ebb` | 6 400 | 0.824 | 0.567 |

Le run v2 a une meilleure précision (0.567 contre 0.543) et une meilleure exactitude (0.897 contre 0.882), mais un recall légèrement plus faible (0.824 contre 0.838). Il ne faut pas conclure trop vite que la v2 est « meilleure » : les deux versions n'ont pas le même nombre de relevés, donc les ensembles d'entraînement et de test ne sont pas identiques. Une comparaison honnête demanderait un jeu de test commun et indépendant.

Comme une panne manquée reste l'erreur la plus coûteuse, je garde provisoirement le recall de la v1. La différence est faible, et la décision finale dépendra du coût réel des fausses alertes.

## 5. Décision : l'ADR 004

L'ADR `docs/adr/004-choix-du-modele.md` retient la régression logistique avec `C=1.0` et un seuil de `0.2`, sur le run `hilarious-bear-847`. Il documente aussi la comparaison avec la v2 (`fun-dove-613`) et les conséquences : plus de fausses alertes sur la v1, des jeux de test différents, et la nécessité de valider sur des données représentatives avant un déploiement réel.

## 6. Questions de compréhension

**1. Git, DVC et MLflow : que versionne chacun ?**  
Git versionne le code, les fichiers de configuration, les ADR et les petits fichiers `.dvc`. DVC versionne le contenu des données volumineuses et permet de retrouver une version précise. MLflow versionne les entraînements : paramètres, métriques, empreinte des données, modèle et environnement Python. Les trois se complètent : Git dit quel code et quel reçu DVC ont été commités, DVC fournit les données, MLflow fournit le run et le modèle.

**2. Pourquoi le remote DVC est-il ajouté avec `--local` ?**  
Le chemin `C:/dvc-stockage` est propre à ma machine. L'écrire dans un fichier versionné imposerait ce chemin à tout le groupe. `--local` place la configuration dans `.dvc/config.local`, ignoré par Git. Pour partager les données, il faudrait un remote accessible à tous (S3, Azure, serveur SSH ou dossier réseau) et les identifiants correspondants.

**3. Livrer un modèle, c'est trois choses. Lesquelles, et où sont-elles ?**  
Le modèle entraîné (`models/model.joblib`, et l'artefact `model` du run MLflow), son contrat d'entrée et de prétraitement (`models/model_info.json` et le pipeline scikit-learn qui contient le scaler), et son environnement logiciel (`requirements.txt`, avec `scikit-learn==1.8.0`, également enregistré par MLflow). Le modèle seul ne suffit pas : sans le contrat ni les versions, il peut produire des résultats faux ou refuser de se charger.

## 7. Point Git

- **Dépôt :** [projet-deploiement-](https://github.com/yahyaLago/projet-deploiement-)
- **Dossier :** `tp/tp5`
- **Mon fichier :** `CR_TP5_Mazine_CHATER.md`
- **Branche :** `main`, ajout direct sans branche personnelle
- **Pull request :** aucune, le fichier est ajouté directement sur `main`
- **Tag :** `tp5`
- **Fichiers exclus :** `.venv`, `data/sensors.csv`, `models/`, `mlflow.db`, `mlruns/`, `.dvc/cache/`
- **Fichiers versionnés :** `.dvc/`, `.dvcignore`, `data/sensors.csv.dvc`, le code et les ADR

## 8. Choix techniques et justifications

| Choix | Pourquoi |
|---|---|
| MLflow plutôt qu'un journal maison | MLflow fournit l'interface de comparaison, le stockage des modèles et la capture des dépendances sans écrire d'outil. Un fichier CSV de résultats aurait demandé de maintenir le format, l'interface et la sérialisation. |
| Base SQLite locale (`mlflow.db`) | Aucun serveur à installer pour un TP solo. SQLite suffit pour quelques dizaines de runs. Un serveur de tracking devient utile dès que plusieurs personnes doivent voir les mêmes runs. |
| Un seul experiment `maintai` | Tous les runs du projet sont comparables dans la même vue. Créer un experiment par essai aurait fragmenté la comparaison. |
| Enregistrer `data_md5` avec chaque run | Les métriques seules ne disent pas sur quelles données elles ont été obtenues. L'empreinte relie le run au fichier `.dvc` et rend la comparaison v1/v2 vérifiable. |
| Enregistrer le modèle dans le run | Le run ne sert pas seulement de tableau de chiffres : on peut recharger le modèle et vérifier qu'il prédit bien. C'est aussi ce que testent les tests de tracking. |
| `input_example` | Il documente la forme et les types attendus, et MLflow peut vérifier la signature au rechargement. |
| `skops_trusted_types` limité à `Tree` | La forêt contient des objets `Tree` que la sérialisation sécurisée refuse par défaut. Autoriser uniquement ce type évite d'ouvrir la porte à tous les types Python. |
| `file_md5` par blocs de 1 Mio | Le calcul reste identique au MD5 de DVC, mais ne charge pas tout le CSV en mémoire. Sur un gros fichier, c'est la différence entre un calcul lent et un pic mémoire. |
| Seuil 0.2 pour le run retenu | Le seuil 0.3 rate plus de pannes. Le 0.2 augmente le recall, au prix de fausses alertes. C'est cohérent avec le coût métier d'une panne manquée. |
| Comparer forêt et régression logistique | La forêt est un modèle plus flexible, mais elle n'est utile que si elle apporte un gain mesurable. Sur ces données, son recall est inférieur ; la régression logistique reste plus simple à expliquer. |
| Pas de `GridSearchCV` | Le TP demande de comparer quelques réglages interprétables, pas d'optimiser à l'aveugle. Quatre runs ciblés suffisent pour voir l'effet du seuil, de `C` et du modèle. Une recherche exhaustive aurait coûté du temps et risqué de surapprendre le jeu de test. |
| `dvc init --subdir` | Isole DVC dans `tp/tp5`. Sans `--subdir`, le `.dvc` serait à la racine et mélangerait les données de tous les TP. |
| Remote DVC `--local` | Le chemin du stockage dépend de la machine. `--local` évite de versionner un chemin personnel tout en gardant la configuration utile au fonctionnement local. |
| Versionner `.dvc` et pas le CSV | Le `.dvc` est petit, lisible et se compare dans un diff. Le CSV est lourd et change en entier. Git garde l'historique des versions, DVC garde le contenu. |
| `dvc add` après chaque régénération | La commande recalcule le MD5 et met à jour le reçu. C'est elle qui crée une nouvelle version identifiable, à committer avec le code ou l'ADR correspondant. |
| `dvc checkout` pour revenir à une version | La commande restaure les octets exacts depuis le cache, sans relancer la génération. On est sûr de retrouver les mêmes données, pas une approximation produite par un autre seed. |
| `dvc pull` après suppression du cache | Cela vérifie que le remote contient bien les données et qu'un coéquipier peut les récupérer. Un cache local seul ne prouve pas que le versionnement est partagé. |
| ADR 004 | La décision est écrite avec les chiffres, les alternatives et les conséquences. Un run MLflow seul ne dit pas pourquoi on l'a choisi ni ce qu'on accepte de perdre. |

## 9. Ce que je retiens

MLflow et DVC répondent à deux questions différentes. MLflow dit quel entraînement a produit un modèle, avec quels paramètres et quelles métriques. DVC dit sur quelle version exacte des données cet entraînement a été fait. Le lien entre les deux est l'empreinte MD5 : sans elle, un bon score reste impossible à reproduire.

Le point le plus utile du TP est cette traçabilité. Avant, je comparais des scores dans un terminal et je perdais le contexte. Maintenant, je peux retrouver un run, recharger son modèle et savoir sur quel fichier il a été entraîné.

Ce qui reste ouvert : le choix du seuil dépend du coût réel des pannes et des fausses alertes, que je ne connais pas. Et la comparaison v1/v2 n'est pas parfaite, car les jeux de test changent. Pour aller plus loin, il faudrait un jeu de test commun, puis un vrai stockage DVC partagé pour que toute l'équipe travaille sur les mêmes données.
