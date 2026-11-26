"""Exécuter une seule fois depuis Ahmed_RAOUI, sur une branche personnelle."""
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
def run(*args):
    result = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, flush=True)
    return result.stdout
def py(*args):
    return run(sys.executable, *args)
def commit(msg):
    run("git", "add", "--", ".")
    run("git", "commit", "-m", msg)
    return run("git", "rev-parse", "HEAD").strip()
def md5():
    return hashlib.md5(Path("data/sensors.csv").read_bytes()).hexdigest()
def count():
    return len(pd.read_csv("data/sensors.csv"))
def train(label, *args):
    out = py("-m", "maintai.train", *args)
    rid = re.search(r"Run MLflow : (\S+)", out).group(1)
    import mlflow
    r = mlflow.get_run(rid)
    assert r.data.params["data_md5"] == md5()
    return dict(label=label, id=rid, **r.data.params, **r.data.metrics)
if Path(".dvc").exists():
    raise SystemExit("DVC existe déjà : ne pas relancer ce script sans vérifier les commits précédents.")
if run("git","branch","--show-current").strip() in ("main","master",""):
    raise SystemExit("Créez d'abord votre branche personnelle.")
# Tests et entraînements dans des conditions par défaut.
for k in ("MAINTAI_DATA_PATH","MAINTAI_MODELS_DIR","MAINTAI_THRESHOLD","MLFLOW_TRACKING_URI"):
    os.environ.pop(k,None)
py("-m","maintai.dataset")
tests=py("-m","pytest")
runs=[train("v1 défaut"),train("v1 C=0.01","--C","0.01"),
      train("v1 seuil 0.2","--threshold","0.2"),train("v1 forêt","--model","forest")]
run("dvc","init","--subdir")
commit("TP5 Ahmed RAOUI : initialisation DVC et code")
run("dvc","add","data/sensors.csv")
h1=md5()
receipt=Path("data/sensors.csv.dvc").read_text()
assert h1 in receipt
c1=commit("TP5 Ahmed RAOUI : données v1")
storage=Path.home()/"dvc-stockage-ahmed-tp5"
storage.mkdir(exist_ok=True)
run("dvc","remote","add","--local","-d","stockage",str(storage))
run("dvc","push")
py("-m","maintai.dataset","--n","8000","--seed","7")
status=run("dvc","status")
run("dvc","add","data/sensors.csv")
h2=md5()
assert h2 in Path("data/sensors.csv.dvc").read_text()
c2=commit("TP5 Ahmed RAOUI : données v2")
run("dvc","push")
runs.append(train("v2 défaut"))
run("git","checkout",c1,"--","data/sensors.csv.dvc")
run("dvc","checkout")
assert count()==5000 and md5()==h1
run("git","checkout","HEAD","--","data/sensors.csv.dvc")
run("dvc","checkout")
assert count()==8000 and md5()==h2
Path("data/sensors.csv").unlink()
shutil.rmtree(".dvc/cache")
pull=run("dvc","pull")
assert count()==8000 and md5()==h2
best=max(runs[:4],key=lambda r:(r["recall"],r["precision"]))
import sklearn
table="\n".join(f'| {r["label"]} | {r["recall"]:.3f} | {r["precision"]:.3f} | {r["accuracy"]:.3f} | `{r["id"]}` | `{r["data_md5"][:8]}` |' for r in runs)
report=f"""# Compte rendu TP5 — Ahmed RAOUI

## Tests
```text
{tests.strip().splitlines()[-1]}
```
Le starter comporte cinq tests de suivi qui nécessitent l'implémentation de log_run.
L'installation editable fait pointer maintai vers ce dossier TP5 plutôt que le TP4.

## MLflow
| Run | Recall | Precision | Accuracy | Identifiant | MD5 |
|---|---:|---:|---:|---|---|
{table}

Choix sur v1 : {best['label']}, recall {best['recall']:.3f}, précision {best['precision']:.3f}.
Une panne manquée est plus coûteuse qu'une fausse alerte. La forêt est comparée sur les mêmes données.
Version scikit-learn utilisée : {sklearn.__version__}. Le modèle MLflow conserve ses dépendances pour éviter les incompatibilités.
Les fichiers mlflow.db et mlruns ne doivent pas aller dans Git.

## DVC
Reçu v1 :
```yaml
{receipt}
```
Le MD5 du reçu est identique au paramètre data_md5 des quatre runs v1.
Le CSV reste hors Git, le reçu léger est versionné.
Après modification :
```text
{status}
```
| Version | Commit | MD5 | Lignes |
|---|---|---|---:|
| v1 | `{c1}` | `{h1[:8]}` | 5000 |
| v2 | `{c2}` | `{h2[:8]}` | 8000 |

Retour v1 puis v2 vérifié par nombre de lignes et MD5.
Après suppression du CSV et du cache, dvc pull a restauré la v2 :
```text
{pull}
```

## Comparaison v1/v2 à réglages identiques
| Version | MD5 | n_train | Recall | Precision |
|---|---|---:|---:|---:|
| v1 | {h1[:8]} | {runs[0]['n_train']} | {runs[0]['recall']:.3f} | {runs[0]['precision']:.3f} |
| v2 | {h2[:8]} | {runs[4]['n_train']} | {runs[4]['recall']:.3f} | {runs[4]['precision']:.3f} |

Les jeux de test diffèrent : on ne peut pas conclure à une amélioration intrinsèque sans évaluation sur un jeu commun indépendant.

## Compréhension
Git versionne le code et les reçus, DVC les données, MLflow les entraînements et modèles.
Le remote local évite de publier un chemin personnel ; un stockage partagé serait nécessaire au groupe.
Le code, les données et le modèle sont retrouvables via Git, DVC et MLflow.
Le MD5 relie le run à un reçu DVC dans l'historique Git.

## Rendu
Pull request et tag tp5 : à vérifier après le push et la fusion du groupe.
"""
Path("compte_rendu_Ahmed_RAOUI.md").write_text(report,encoding="utf-8")
Path("docs/adr/004-choix-du-modele.md").write_text(f"""# ADR 004 : choix du modèle MaintAI

Auteur : Ahmed RAOUI

## Contexte
Une panne manquée est plus coûteuse qu'une fausse alerte.

## Options
Régression logistique par défaut, C=0.01, seuil 0.2 et forêt aléatoire, comparées sur v1.

## Décision
{best['label']} ; modèle `{best['model']}`, seuil `{best['threshold']}`.
Recall : {best['recall']:.3f} ; précision : {best['precision']:.3f}.
Run : `{best['id']}`.
data_md5 : `{best['data_md5']}`.

## Conséquences
Priorité au recall, quitte à accepter davantage de fausses alertes.
Surveiller la précision et la dérive ; réévaluer sur un jeu indépendant commun.
""",encoding="utf-8")
commit("TP5 Ahmed RAOUI : compte rendu et ADR avec résultats vérifiés")
print("Terminé : vérifier les fichiers et pousser la branche.")
