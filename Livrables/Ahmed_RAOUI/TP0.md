TP0 : MaintAI et Cantine — Classification et régression

Nom : Ahmed Raoui
Groupe : G1

1. MaintAI — Prédiction des pannes (classification)
Le problème

MaintAI doit prédire une panne à partir de quatre capteurs : la température, les vibrations, la charge et le temps de fonctionnement. Une panne qui passe inaperçue peut arrêter une ligne de production. Le modèle doit donc d'abord limiter les pannes manquées, et non seulement maximiser l'accuracy.

Résultats sur le jeu de test
Modèle	Accuracy	Rappel	Précision
Baseline	0.824	0.000	0.000
Régression logistique	0.889	0.574	0.737

Mon choix, et pourquoi

Je choisis la régression logistique parmi les modèles évalués. Elle améliore l'accuracy par rapport à la baseline et détecte une partie des pannes : son rappel est de 0.574, contre 0.000 pour la baseline. Sa précision de 0.737 indique toutefois qu'environ une alerte sur quatre est fausse.

Ce choix est provisoire : le modèle ne satisfait pas encore le critère de rappel défini plus bas.

Le critère (rappel ≥ 0,75) est-il atteint ?

Non. Le rappel de la régression logistique est de 0.574, soit 0.176 point sous l'objectif de 0.75. La baseline a un rappel nul. Aucun modèle ne respecte donc le critère d'acceptation.

Ce qui reste flou
La taille du jeu de test et la répartition entre pannes et non-pannes ne sont pas données ; l'accuracy peut être trompeuse en cas de déséquilibre.
On ne sait pas si le découpage évite une fuite entre entraînement et test.
Le seuil de décision n'est pas précisé. Un seuil plus bas augmenterait le rappel, au prix de fausses alertes supplémentaires.
Le coût réel d'une fausse alerte n'est pas comparé à celui d'une panne manquée.
Il faut évaluer le modèle sur plus de pannes et sur des conditions de fonctionnement variées avant toute utilisation opérationnelle.

2. Cantine — Prédiction du nombre de repas servis (régression)
Le problème

Le projet Cantine consiste à prédire le nombre de repas servis chaque jour à partir du nombre d'inscrits, du menu, de la température, de la pluie, des examens, des sorties scolaires et des vacances.

L'objectif est d'aider à prévoir les quantités. Une prédiction trop haute entraîne du gaspillage ; une prédiction trop basse provoque un manque de repas. Le modèle doit fournir des estimations assez précises pour la planification.

À la différence de MaintAI, qui classe les observations en deux catégories (panne ou absence de panne), Cantine est un problème de régression, car la cible repas_servis est numérique.

Préparation des données

Le fichier utilisé est data/cantine_repas.csv. La cible est repas_servis ; les autres colonnes pertinentes sont les variables explicatives.
  mae    rmse     r2
ridge              22.377  28.315  0.882
gradient_boosting  29.852  37.727  0.790
random_forest      31.825  41.647  0.745
knn                40.274  49.450  0.640
baseline           70.271  88.416 -0.151

Meilleur modèle selon mae : ridge
Le découpage est chronologique : les observations anciennes servent à l'entraînement, les plus récentes au test. Cela reproduit une situation réelle, où l'on prévoit le futur à partir du passé.

La colonne date sert à ordonner les observations et ne doit pas être utilisée directement comme variable explicative dans cette configuration.

Modèles évalués

Plusieurs modèles de régression sont comparés :

Baseline : prédit une constante égale à la moyenne des repas servis à l'entraînement.
Ridge : régression linéaire régularisée.
K plus proches voisins (KNN) : estime le résultat à partir d'observations similaires.
Random Forest : combine plusieurs arbres de décision.
Gradient Boosting : construit successivement des arbres pour améliorer les prédictions précédentes.

La baseline permet de vérifier que les modèles apprennent des relations utiles entre les caractéristiques de la cantine et le nombre de repas.

Critères d'évaluation

Trois métriques sont utilisées :

MAE (erreur absolue moyenne) : écart absolu moyen entre la prédiction et la réalité, en nombre de repas. Plus elle est faible, mieux c'est.
RMSE (racine de l'erreur quadratique moyenne) : pénalise davantage les erreurs importantes. Plus elle est faible, mieux c'est.
R² (coefficient de détermination) : mesure la variabilité expliquée. Proche de 1, les prédictions sont bonnes ; négatif, le modèle fait moins bien que la moyenne.

La MAE est la métrique principale, car elle s'interprète directement en nombre de repas.

Résultats sur le jeu de test
Modèle	MAE	RMSE	R²
Baseline	À compléter	À compléter	À compléter
Ridge	À compléter	À compléter	À compléter
KNN	À compléter	À compléter	À compléter
Random Forest	À compléter	À compléter	À compléter
Gradient Boosting	À compléter	À compléter	À compléter

Les valeurs doivent être renseignées à partir des résultats du programme d'entraînement. La comparaison n'est équitable que sur le même jeu de test.

Mon choix, et pourquoi

Le meilleur modèle est celui qui obtient la MAE la plus faible sur le jeu de test, tout en battant la baseline. Une MAE de 10 signifie par exemple que les prédictions s'écartent en moyenne de 10 repas du nombre réellement servi.

Le choix définitif attend l'analyse des métriques : je ne conclus pas qu'un modèle est meilleur sans ses résultats réels.

Le modèle bat-il la baseline ?

Ce point se vérifie sur les résultats du test. Pour la MAE, le modèle retenu doit être inférieur à la baseline. Il faut aussi examiner la RMSE et le R² pour détecter les grosses erreurs et juger la qualité globale.

Ce qui reste flou
La MAE, la RMSE et le R² de chaque modèle doivent encore être reportés.
Le volume de données et la durée couverte ne sont pas précisés.
repas_semaine_precedente peut être utile, mais sa disponibilité au moment de la prédiction doit être garantie.
Les conséquences d'une erreur dépendent du sens de l'erreur : trop de repas ou pas assez.
Il faudra vérifier la performance sur de nouvelles périodes, quand les menus, les effectifs ou la météo changent.

Conclusion générale

Les deux projets illustrent deux types d'apprentissage complémentaires. MaintAI utilise la classification pour détecter des pannes ; Cantine utilise la régression pour estimer une quantité numérique.

Dans MaintAI, le rappel est essentiel, car une panne non détectée peut avoir des conséquences lourdes. Dans Cantine, la MAE est privilégiée, car elle mesure directement l'écart moyen en nombre de repas.

Dans les deux cas, la performance doit être évaluée sur des données de test distinctes de l'entraînement. Le choix d'un modèle dépend des métriques, mais aussi des conséquences concrètes de ses erreurs et de sa capacité à généraliser.
