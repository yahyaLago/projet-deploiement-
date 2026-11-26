# Documentation — TP5

## Deux problèmes différents

Un modèle n'est pas reproductible si l'on ne sait pas :

1. **avec quels réglages** il a été entraîné ;
2. **sur quelle version des données** il a été entraîné.

Le TP5 traite ces deux points avec deux outils complémentaires :

- **MLflow** garde la trace des entraînements ;
- **DVC** garde la trace des données.

## MLflow : comparer les entraînements

Un *run* est une exécution de `python -m maintai.train`. `log_run` y écrit :

- les paramètres : type de modèle, `C`, seuil, taille de l'entraînement ;
- l'empreinte `data_md5` du CSV ;
- les métriques calculées sur le jeu de test ;
- le modèle sérialisé, dans le format skops, avec les versions des
  bibliothèques.

L'interface `mlflow ui` affiche un tableau : on peut trier par rappel,
comparer un seuil à 0,2 et un seuil à 0,3, ou vérifier qu'une forêt fait
mieux qu'une régression logistique sur les mêmes données.

**Pourquoi le modèle dans MLflow ?** Le fichier `model.joblib` sert à la
production locale. MLflow sert à l'historique : savoir quel modèle a produit
quelle métrique, et pouvoir le recharger plus tard.

**Pourquoi l'empreinte des données ?** Deux runs avec les mêmes paramètres
mais des données différentes ne sont pas comparables. L'empreinte MD5 est
la même que celle écrite par DVC : elle fait le lien entre les deux outils.

## DVC : versionner les données

Git n'est pas fait pour stocker des fichiers binaires volumineux ou
changeants. DVC stocke le fichier ailleurs et ne versionne qu'un petit
fichier `.dvc` qui contient :

- l'empreinte MD5 ;
- la taille ;
- le nom du fichier.

`dvc checkout` reconstruit le CSV correspondant au `.dvc` courant. On peut
donc changer de version de données avec Git, sans mettre le CSV dans
l'historique Git.

## Choix techniques

**Un seul point d'entrée pour le suivi.** Tout l'appel à MLflow est dans
`tracking.py`. Si l'outil change, seul ce fichier est à modifier.

**Le suivi ne bloque pas l'entraînement local.** Les artefacts classiques
(`model.joblib`, `metrics.json`) sont toujours écrits. MLflow est un
historique, pas une dépendance de la prédiction.

**Le seuil est un paramètre du run.** Il influence directement le rappel :
le comparer explicitement évite de croire qu'un modèle est meilleur alors
que seul le seuil a changé.

## Limites

- `mlflow.db` et `mlruns/` ne sont pas versionnés : l'historique reste local.
- Le registre de modèles MLflow n'est pas utilisé (pas de statut
  « production »).
- Le stockage DVC est local ; une équipe utiliserait un stockage partagé.
