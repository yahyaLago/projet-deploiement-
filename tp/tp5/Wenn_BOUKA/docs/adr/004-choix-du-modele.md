# ADR 004 : choix du modèle et du seuil d'alerte de MaintAI

Date : 20/11/2026 · Auteur : Wenn BOUKA

## Contexte

MaintAI alerte quand un relevé de capteurs annonce une panne. Une panne manquée (arrêt de production, réparation lourde) coûte bien plus qu'une fausse alerte (une inspection pour rien). Le critère prioritaire est donc le **recall**, la précision restant sous surveillance pour que les alertes gardent du sens. L'accuracy n'est pas un bon critère : la baseline qui ne prédit jamais de panne atteint 0.864 d'accuracy avec un recall de 0.

Tous les runs sont tracés dans MLflow (expérience `maintai`), avec la version des données (`data_md5`) suivie par DVC : v1 = 5 000 relevés (`b7fec427…`), v2 = 8 000 relevés (`31ef5ebb…`).

## Options étudiées (données v1, `n_train = 4000`)

| Modèle | C | Seuil | Recall | Précision | Accuracy | Run |
|---|---:|---:|---:|---:|---:|---|
| Régression logistique | 1 | 0,3 | 0.750 | 0.622 | 0.904 | `sneaky-horse-146` |
| Régression logistique | 1 | 0,2 | 0.838 | 0.543 | 0.882 | `valuable-rat-309` |
| Régression logistique | 1 | **0,15** | **0.875** | 0.500 | 0.864 | `grandiose-bee-356` |
| Régression logistique | 0,01 | 0,3 | 0.691 | 0.653 | 0.908 | `victorious-hare-456` |
| Forêt aléatoire | — | 0,3 | 0.728 | 0.562 | 0.886 | `indecisive-mare-42` |
| Forêt aléatoire | — | 0,2 | 0.831 | 0.479 | 0.854 | `beautiful-sloth-685` |

## Décision

**Régression logistique, `C=1`, seuil d'alerte 0,15.** Run de référence : `grandiose-bee-356` (`run_id = cf595aee40fa4219817e00b676dcab3c`, données v1).

- C'est le meilleur recall mesuré : 7 pannes détectées sur 8, contre 6 sur 8 au seuil 0,3.
- La forêt aléatoire, plus lourde à entraîner et à livrer, fait moins bien que la régression logistique à seuil égal. Elle n'est pas retenue.
- Le levier principal est le seuil, pas le modèle : il se règle par la variable `MAINTAI_THRESHOLD`, sans réentraîner.

Vérification sur la v2, même réglage : `polite-horse-748` (`n_train = 6400`) donne recall 0.859, précision 0.506, accuracy 0.874. La tendance est la même ; les écarts (environ 2 points) restent dans ce qu'expliquent des jeux de test différents.

## Conséquences

- **Une fausse alerte pour une vraie** (précision 0.50). C'est acceptable seulement si une inspection est rapide ; à revoir avec l'équipe maintenance si les techniciens se mettent à ignorer les alertes.
- Le seuil a été choisi en lisant le jeu de test. Avant le déploiement, il faut le confirmer sur un jeu de validation séparé, puis mesurer le modèle final sur un jeu de test figé, versionné avec DVC et identique pour toutes les versions des données.
- Toute nouvelle version des données entraîne un nouveau run tracé (`data_md5`), comparé à ce run de référence avant de remplacer le modèle en service.
