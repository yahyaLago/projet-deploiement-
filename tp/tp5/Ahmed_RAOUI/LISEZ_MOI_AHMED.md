# TP5 Ahmed RAOUI

Copier ce dossier dans `tp/tp5/` du dépôt de groupe, sur une branche `tp-ahmed-raoui`.
Depuis ce dossier, activer un environnement Python compatible puis :
```
python -m pip install -r requirements.txt
python -m pip install -e .
python finaliser_tp5.py
```
Le script crée les commits DVC et le rapport final. Exécuter une seule fois sur une branche personnelle.
Si une commande échoue, corriger le problème avant de reprendre manuellement ; ne pas relancer aveuglément.
Puis `mlflow ui` pour vérifier les runs et prendre les captures si demandées.
Ne pas publier le CSV, les modèles, le cache DVC ou la base MLflow.
Le stockage DVC est local : le groupe ne pourra pas récupérer les données depuis un autre PC sans stockage partagé.
