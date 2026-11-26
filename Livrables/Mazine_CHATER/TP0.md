TP0 : MaintAI et Cantine — Classification et régression

Nom : Mazine Chater
Groupe : G1

1. MaintAI — Prédiction des pannes (classification)
Le problème

MaintAI doit prédire une panne à partir de quatre capteurs : la température, les vibrations, la charge et le temps de fonctionnement. Une panne non détectée peut arrêter une ligne de production ; mon objectif est donc de détecter un maximum de pannes, plutôt que de battre un record d'accuracy.

Résultats sur le jeu de test
Modèle	Accuracy	Rappel	Précision
Baseline	0.824	0.000	0.000
Régression logistique	0.889	0.574	0.737

Mon choix, et pourquoi

Je retiens la régression logistique. Elle fait nettement mieux que la baseline sur l'accuracy, mais surtout elle détecte une partie des pannes : son rappel vaut 0.574, alors que la baseline n'en détecte aucune. Sa précision de 0.737 montre qu'une alerte sur quatre environ est fausse, ce qui reste acceptable si une panne coûte plus cher qu'un contrôle inutile.

Je garde ce choix comme provisoire : le modèle n'atteint pas encore le critère de rappel fixé plus bas.

Le critère (rappel ≥ 0,75) est-il atteint ?

Non. Le rappel obtenu est de 0.574, soit 0.176 point sous l'objectif de 0.75. La baseline, avec un rappel nul, en est encore plus loin. Aucun des deux modèles ne respecte donc le critère d'acceptation.

Ce qui reste flou
La taille du jeu de test et la proportion de pannes ne sont pas précisées ; l'accuracy peut tromper quand les classes sont déséquilibrées.
Je ne sais pas si le découpage empêche une fuite entre l'entraînement et le test.
Le seuil de décision n'est pas indiqué. Un seuil plus bas augmenterait le rappel, au risque de multiplier les fausses alertes.
Le coût d'une fausse alerte n'est pas comparé au coût d'une panne manquée.
Il faudrait tester le modèle sur davantage de pannes et dans des conditions variées avant de l'utiliser en production.

2. Cantine — Prédiction du nombre de repas servis (régression)
Le problème

Le projet Cantine consiste à prévoir le nombre de repas servis chaque jour à partir du nombre d'inscrits, du menu, de la température, de la pluie, des examens, des sorties scolaires et des vacances.

L'objectif est d'aider à préparer les bonnes quantités. Prévoir trop haut provoque du gaspillage ; prévoir trop bas laisse des élèves sans repas. Le modèle doit donc rester assez précis pour la planification.

Contrairement à MaintAI, qui classe les observations en deux catégories (panne ou pas de panne), Cantine est un problème de régression : la cible repas_servis est une quantité numérique.

Préparation des données

Le fichier utilisé est data/cantine_repas.csv. La cible est repas_servis ; les autres colonnes pertinentes servent de variables explicatives.
  mae    rmse     r2
ridge              22.377  28.315  0.882
gradient_boosting  29.852  37.727  0.790
random_forest      31.825  41.647  0.745
knn                40.274  49.450  0.640
baseline           70.271  88.416 -0.151

Meilleur modèle selon mae : ridge
Le découpage est chronologique : les observations les plus anciennes entraînent les modèles, les plus récentes servent au test. Cette méthode reproduit une situation réelle, où l'on utilise le passé pour prévoir le futur.

La colonne date sert uniquement à ordonner les observations ; elle ne doit pas être utilisée comme variable explicative dans cette configuration.

Modèles évalués

Plusieurs modèles de régression sont comparés :

Baseline : prédit une valeur constante, la moyenne des repas observés à l'entraînement.
Ridge : régression linéaire régularisée.
K plus proches voisins (KNN) : estime la valeur à partir d'observations similaires.
Random Forest : combine plusieurs arbres de décision.
Gradient Boosting : construit successivement des arbres pour corriger les erreurs précédentes.

La comparaison avec la baseline permet de vérifier que les modèles apprennent une relation utile, et pas seulement une moyenne.

Critères d'évaluation

Trois métriques sont utilisées :

MAE (erreur absolue moyenne) : écart absolu moyen, en nombre de repas. Plus elle est faible, meilleures sont les prédictions.
RMSE (racine de l'erreur quadratique moyenne) : pénalise davantage les grosses erreurs. Plus elle est faible, mieux c'est.
R² (coefficient de détermination) : part de la variabilité expliquée. Proche de 1, le modèle est bon ; négatif, il fait moins bien que la moyenne.

La métrique principale est la MAE, car elle s'interprète directement en nombre de repas.

Résultats sur le jeu de test
Modèle	MAE	RMSE	R²
Baseline	À compléter	À compléter	À compléter
Ridge	À compléter	À compléter	À compléter
KNN	À compléter	À compléter	À compléter
Random Forest	À compléter	À compléter	À compléter
Gradient Boosting	À compléter	À compléter	À compléter

Les valeurs doivent être reprises des résultats du programme d'entraînement. Tous les modèles doivent être comparés sur le même jeu de test.

Mon choix, et pourquoi

Le meilleur modèle sera celui qui obtient la MAE la plus faible sur le jeu de test, à condition de battre la baseline. Une MAE de 10 signifierait par exemple que les prédictions s'écartent en moyenne de 10 repas du nombre réellement servi.

Je ne conclus pas avant d'avoir les résultats réels : un modèle n'est pas meilleur parce qu'il est plus complexe.

Le modèle bat-il la baseline ?

Ce point se vérifie sur les résultats du test. Pour la MAE, le modèle retenu doit être inférieur à la baseline. Il faut aussi regarder la RMSE et le R² pour repérer d'éventuelles grosses erreurs.

Ce qui reste flou
Les métriques de chaque modèle doivent encore être reportées pour permettre une comparaison concrète.
Le volume de données et la période couverte ne sont pas précisés.
repas_semaine_precedente peut aider, mais il faut garantir qu'elle est disponible au moment de la prédiction.
Une erreur de prévision n'a pas les mêmes conséquences selon qu'elle conduit à préparer trop ou trop peu de repas.
Il faudra vérifier la stabilité du modèle lorsque les menus, les effectifs ou la météo changent.

Conclusion générale

Les deux projets illustrent deux familles de problèmes complémentaires. MaintAI fait de la classification pour détecter des pannes ; Cantine fait de la régression pour estimer une quantité.

Pour MaintAI, le rappel est prioritaire, car une panne manquée a un coût élevé. Pour Cantine, la MAE est privilégiée, car elle se lit directement en nombre de repas.

Dans les deux cas, l'évaluation doit se faire sur des données de test séparées de l'entraînement. Le choix d'un modèle dépend autant des métriques que des conséquences concrètes de ses erreurs.
