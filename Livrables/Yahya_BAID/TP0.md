TP0 : MaintAI et Cantine — Classification et régression

Nom : Yahya Baid
Groupe : G1

1. MaintAI — Prédiction des pannes (classification)
Le problème

MaintAI doit prédire une panne à partir de quatre capteurs : la température, les vibrations, la charge et le temps de fonctionnement. Une panne manquée peut arrêter une ligne de production ; il est donc plus important de détecter correctement les pannes que de maximiser uniquement l'accuracy.

Résultats sur le jeu de test
Modèle	Accuracy	Rappel	Précision
Baseline	0.824	0.000	0.000
Régression logistique	0.889	0.574	0.737
Mon choix, et pourquoi

Je retiens la régression logistique comme meilleur modèle parmi ceux évalués. Elle améliore nettement l'accuracy par rapport à la baseline et, surtout, elle détecte une partie des pannes : son rappel est de 0.574, alors que la baseline ne détecte aucune panne. Sa précision de 0.737 signifie cependant qu'une partie des alertes est erronée.

Ce choix reste provisoire pour une mise en production, car le modèle ne respecte pas encore le critère de rappel défini ci-dessous. Il faudrait notamment ajuster le seuil de décision et évaluer ce réglage sur un jeu de validation distinct.

Le critère (rappel ≥ 0,75) est-il atteint ?

Non. Le rappel de la régression logistique est de 0.574, soit 0.176 point en dessous de l'objectif de 0.75. La baseline est encore plus insuffisante avec un rappel nul. Aucun des modèles présentés ne satisfait donc le critère d'acceptation.

Ce qui reste flou
La taille exacte du jeu de test et la répartition entre pannes et non-pannes ne sont pas indiquées ; l'accuracy peut être trompeuse si les classes sont déséquilibrées.
On ne sait pas si le découpage des données empêche une fuite entre l'entraînement et le test.
Le seuil de décision n'est pas précisé. Un seuil plus bas pourrait augmenter le rappel, au prix d'une baisse possible de la précision.
Le coût réel d'une fausse alerte n'est pas comparé au coût d'une panne manquée.
Il faut tester le modèle sur davantage de pannes et sur des conditions de fonctionnement variées avant toute utilisation opérationnelle.
2. Cantine — Prédiction du nombre de repas servis (régression)
Le problème

Le projet Cantine consiste à prédire le nombre de repas servis chaque jour à partir des informations disponibles, telles que le nombre d'inscrits, le menu, la température, la pluie, les examens, les sorties scolaires et les vacances.

L'objectif est d'aider à mieux prévoir les quantités de repas à préparer. Une prédiction trop élevée peut entraîner du gaspillage alimentaire, tandis qu'une prédiction trop faible peut provoquer un manque de repas. Le modèle doit donc fournir des estimations suffisamment précises pour faciliter la planification.

Contrairement au projet MaintAI, qui cherche à classer les observations en deux catégories (panne ou absence de panne), le projet Cantine est un problème de régression, car la variable cible repas_servis est numérique.

Préparation des données

Le fichier utilisé est data/cantine_repas.csv. La variable cible est repas_servis, et les autres colonnes pertinentes servent de variables explicatives.
  mae    rmse     r2
ridge              22.377  28.315  0.882
gradient_boosting  29.852  37.727  0.790
random_forest      31.825  41.647  0.745
knn                40.274  49.450  0.640
baseline           70.271  88.416 -0.151

Meilleur modèle selon mae : ridge
Le découpage des données est chronologique : les observations les plus anciennes servent à entraîner les modèles, tandis que les observations les plus récentes sont utilisées pour les tester. Cette méthode est adaptée à la prévision, car elle reproduit mieux une situation réelle dans laquelle on utilise les données passées pour prédire le futur.

La colonne date sert à ordonner les observations et ne doit pas être utilisée directement comme variable explicative dans la configuration actuelle.

Modèles évalués

Plusieurs modèles de régression sont comparés :

Baseline : prédit une valeur constante égale à la moyenne des repas servis dans les données d'entraînement.
Ridge : modèle de régression linéaire régularisé.
K plus proches voisins (KNN) : estime le résultat à partir d'observations similaires.
Random Forest : combine plusieurs arbres de décision pour produire une prédiction.
Gradient Boosting : construit successivement des arbres afin d'améliorer les prédictions précédentes.

La comparaison avec la baseline permet de vérifier si les modèles apprennent des relations utiles entre les caractéristiques de la cantine et le nombre de repas servis.

Critères d'évaluation

Trois métriques sont utilisées pour évaluer les prédictions :

MAE (erreur absolue moyenne) : mesure l'écart absolu moyen entre le nombre de repas prédit et le nombre réellement servi. Elle s'exprime en nombre de repas. Plus elle est faible, meilleures sont les prédictions.
RMSE (racine de l'erreur quadratique moyenne) : pénalise davantage les erreurs importantes. Plus elle est faible, mieux c'est.
R² (coefficient de détermination) : mesure dans quelle mesure le modèle explique la variabilité des observations. Une valeur proche de 1 indique de bonnes prédictions, tandis qu'une valeur négative indique que le modèle fait moins bien que la prédiction de la moyenne sur le jeu évalué.

La métrique principale retenue est la MAE, car elle permet d'interpréter directement l'erreur moyenne en nombre de repas.

Résultats sur le jeu de test
Modèle	MAE	RMSE	R²
Baseline	À compléter	À compléter	À compléter
Ridge	À compléter	À compléter	À compléter
KNN	À compléter	À compléter	À compléter
Random Forest	À compléter	À compléter	À compléter
Gradient Boosting	À compléter	À compléter	À compléter

Les valeurs doivent être renseignées à partir des résultats produits par le programme d'entraînement. Il est nécessaire de comparer les modèles sur le même jeu de test pour obtenir une évaluation équitable.

Mon choix, et pourquoi

Le meilleur modèle sera celui qui obtient la MAE la plus faible sur le jeu de test. Il devra également être comparé à la baseline afin de vérifier qu'il apporte une amélioration réelle.

Par exemple, une MAE de 10 signifierait que les prédictions s'écartent en moyenne d'environ 10 repas du nombre réellement servi. Cette interprétation permet de relier directement les résultats techniques aux besoins de la cantine.

Le choix définitif du modèle reste à effectuer après l'analyse des métriques obtenues. Il ne faut pas conclure qu'un modèle est meilleur sans disposer de ses résultats réels.

Le modèle bat-il la baseline ?

Ce point doit être vérifié à partir des résultats du test. Pour la MAE, le modèle retenu doit obtenir une valeur inférieure à celle de la baseline. Une amélioration de la MAE indique que le modèle réduit l'erreur absolue moyenne par rapport à une prédiction constante fondée sur la moyenne de l'entraînement.

Il est également utile d'examiner la RMSE et le R² afin de détecter d'éventuelles erreurs importantes et de mieux comprendre la qualité des prédictions.

Ce qui reste flou
La MAE, la RMSE et le R² de chaque modèle doivent encore être reportés pour permettre une comparaison concrète.
Le volume de données disponible et la durée couverte par les observations ne sont pas précisés.
La variable repas_semaine_precedente peut être utile pour la prévision, mais sa disponibilité au moment de la prédiction doit être garantie.
Les erreurs de prévision peuvent avoir des conséquences différentes selon qu'elles conduisent à préparer trop ou trop peu de repas.
Il faudra vérifier les performances sur de nouvelles périodes pour s'assurer que le modèle reste fiable lorsque les menus, les effectifs ou les conditions météorologiques changent.
Conclusion générale

Les deux projets illustrent deux types de problèmes d'apprentissage automatique complémentaires. MaintAI utilise la classification pour détecter des pannes, tandis que le projet Cantine utilise la régression pour estimer une quantité numérique.

Dans MaintAI, le rappel est essentiel, car une panne non détectée peut entraîner des conséquences importantes. Dans le projet Cantine, la MAE est privilégiée parce qu'elle mesure directement l'écart moyen en nombre de repas.

Dans les deux cas, la performance doit être évaluée sur des données de test distinctes de celles utilisées pour l'entraînement. Le choix d'un modèle doit tenir compte non seulement des métriques, mais aussi des conséquences concrètes de ses erreurs et de sa capacité à généraliser à de nouvelles observations.