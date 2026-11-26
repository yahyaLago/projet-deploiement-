# ADR 002 : bornes des variables et comportement si le modèle est absent

Date : 05/11/2026 · Auteurs : Yahya Baid

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes. Une valeur impossible doit être refusée avant d'atteindre le modèle, sans rejeter une machine réelle simplement parce qu'elle sort des valeurs vues à l'entraînement. L'API peut aussi démarrer alors que le modèle n'a pas encore été entraîné.

## Options étudiées

### Comment fixer les bornes
1. **Bornes physiques** : on refuse ce qu'un moteur ou un capteur ne peut pas afficher. Une machine plus chaude que d'habitude passe et peut déclencher une alerte. En contrepartie, certaines valeurs acceptées restent loin de celles vues à l'entraînement.
2. **Minimum et maximum de `sensors.csv`** : simple à calculer, mais une machine réelle légèrement hors de ces valeurs serait refusée, alors que c'est peut-être celle qui va tomber en panne. Les bornes changeraient aussi à chaque nouveau jeu de données.

### Modèle absent
1. **Démarrer et répondre 503** : `/health` reste joignable et indique `model_loaded: false`, et le message dit quoi faire. En contrepartie, l'API semble lancée alors qu'elle ne peut pas encore prédire : il faut surveiller `/health`.
2. **Refuser de démarrer** : le problème est visible immédiatement au lancement. Mais on perd `/health` et `/docs`, et le client ne reçoit qu'une connexion refusée, sans explication.

## Décision

Bornes physiques, parce qu'une machine anormale doit être évaluée et non rejetée :

| Variable | Minimum | Maximum | Justification |
|---|---|---|---|
| `temperature_c` | -40 | 150 | Démarrage à froid dans un local non chauffé ; au-delà de 150 °C, on soupçonne un capteur défaillant plutôt qu'une mesure normale de moteur. |
| `vibration_mm_s` | 0 | 50 | Une vitesse de vibration mesurée n'est pas négative ; 50 mm/s laisse une large marge pour une machine très dégradée. |
| `load_pct` | 0 | 100 | Pourcentage de la capacité nominale, de l'arrêt à la pleine charge. |
| `runtime_hours` | 0 | 100 000 | Un compteur cumulé n'est pas négatif ; 100 000 h représentent environ 11 ans de marche continue. |

Modèle absent : **démarrer et répondre 503**, parce que l'API reste diagnostiquable et que le client reçoit une réponse qui explique quoi faire.

Tous les champs sont de type `float` : avec `int`, 15000,5 heures seraient refusées.

## Conséquences
- Un relevé dans les bornes mais très éloigné des données d'entraînement reste accepté : sa prédiction est alors moins fiable.
- La limite de 100 % refuse une surcharge réelle. Si l'atelier relève des charges supérieures à la capacité nominale, il faudra relever cette borne.
- Ces bornes sont des choix raisonnés, à faire confirmer par les fiches techniques des machines.
- Il faudra surveiller `/health` en production, puisque l'API démarre même sans modèle.
