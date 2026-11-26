# Documentation — TP1

## Le problème

Une panne manquée coûte plus cher qu'une fausse alerte : le modèle doit donc
surtout **détecter** les pannes. C'est pour cela que le rappel (*recall*) est
la métrique de référence, et non l'accuracy seule.

Un relevé contient quatre variables :

| Variable | Sens | Plage acceptée |
|---|---|---|
| `temperature_c` | température du moteur | -40 à 150 °C |
| `vibration_mm_s` | vitesse de vibration | 0 à 50 mm/s |
| `load_pct` | charge de la machine | 0 à 100 % |
| `runtime_hours` | heures de fonctionnement | 0 à 100 000 h |

## Le pipeline

1. `dataset.py` fabrique un CSV synthétique reproductible (`SEED = 42`).
2. `data.py` vérifie les colonnes, puis découpe 80 % / 20 % en conservant la
   proportion de pannes dans chaque partie (*stratification*).
3. `train.py` ajuste un `StandardScaler` puis une régression logistique.
   Le scaler est **dans** le pipeline : le fichier `model.joblib` contient
   donc tout ce qu'il faut pour prédire, sans étape oubliée.
4. `predict.py` recharge le modèle et applique le seuil d'alerte.
5. `api/main.py` charge le modèle une seule fois au démarrage et répond.

## Choix techniques

**Régression logistique plutôt qu'un modèle plus complexe.** Elle est rapide,
interprétable et donne une probabilité directement exploitable. Sur des
données de capteurs peu nombreuses, un modèle plus lourd n'apporte pas de
gain évident et complique la mise en production.

**Seuil réglable (`MAINTAI_THRESHOLD`, 0,3 par défaut).** Le seuil 0,5 de
scikit-learn n'est pas adapté : il privilégie la précision. En maintenance,
on préfère alerter un peu trop souvent. Le seuil fait partie du contrat
enregistré dans `model_info.json`, donc la prédiction et l'évaluation
utilisent bien le même.

**Validation par Pydantic.** Les plages de valeurs sont déclarées dans
`schemas.py`. FastAPI renvoie automatiquement un 422 pour une valeur
absurde, un champ manquant ou un champ en trop. On évite ainsi de laisser
entrer des données impossibles dans le modèle.

**Configuration par variables d'environnement.** Les tests peuvent pointer
vers un dossier temporaire sans modifier le code. `get_settings()` n'est pas
mis en cache : un changement d'environnement est pris en compte au prochain
appel.

**Modèle chargé une seule fois.** La lecture de `model.joblib` est faite au
démarrage (`lifespan`). Si le fichier manque, l'API démarre quand même et
renvoie un 503 explicite sur `/v1/predict` : le service reste observable.

## Limites

- Le jeu de données est synthétique : les résultats mesurent la cohérence du
  pipeline, pas la performance réelle sur des machines.
- Le rappel reste inférieur à l'objectif de 0,75. Un seuil plus bas ou des
  données réelles permettraient de progresser.
- Il n'y a pas encore d'authentification : c'est l'objet du TP2.
