# Projet BigData — Data Lake local

## Présentation

Ce projet met en place une petite infrastructure **Big Data / Data Lake en local**.

L'objectif est de reproduire simplement une architecture de données complète, avec stockage, traitement, historisation, supervision et documentation.

L'architecture principale est la suivante :

```text
OpenCode
   ↓
Fichiers / logs
   ↓
RustFS
   ↓
Apache Spark
   ↓
Apache Iceberg
   ↓
Cache local
   ↓
Streamlit
   ↓
Dashboard
```

En parallèle, **Docsify** permet d'afficher la documentation du projet sous forme de site web :

```text
README / documentation Markdown
              ↓
            Docsify
              ↓
     Documentation web
```

---

# 1. Rôle de chaque partie de l'infrastructure

## OpenCode

OpenCode est utilisé comme assistant de développement.

Il permet notamment de :

- lire les fichiers du projet ;
- créer ou modifier du code ;
- aider à corriger des erreurs ;
- produire des fichiers et des logs.

Dans cette infrastructure, OpenCode est aussi considéré comme une **source de données**.

---

## Dossier `~/BigData`

Le dossier principal du projet est :

```bash
~/BigData
```

Il contient les scripts, la configuration, le dashboard et la documentation.

Exemple :

```text
BigData/
├── README.md
├── dashboard.py
├── spark_dashboard_export.py
├── rustfs_dashboard_export.py
├── sync-opencode-log.sh
├── sync-opencode-s3.sh
├── docker-compose.yml
├── start-all.sh
├── stop-all.sh
├── status-all.sh
├── docs/
│   ├── index.html
│   ├── README.md
│   ├── _sidebar.md
│   └── .nojekyll
└── .venv/
```

---

## Docker

Docker permet d'exécuter RustFS dans un conteneur.

Cela évite d'installer directement RustFS dans le système.

Le fichier :

```text
docker-compose.yml
```

décrit notamment :

- l'image RustFS ;
- les ports ;
- le volume de stockage ;
- la configuration du conteneur.

---

## RustFS

RustFS est le système de stockage principal du projet.

Il est compatible avec le protocole **Amazon S3**.

Le bucket principal utilisé est :

```text
s3://opencode-data
```

RustFS peut stocker :

- des logs ;
- des fichiers JSON ;
- des fichiers Python ;
- des fichiers Parquet ;
- des métadonnées Iceberg ;
- différents fichiers du projet.

Adresses utilisées :

```text
API S3 :
http://localhost:9000

Interface RustFS :
http://localhost:9001
```

En résumé :

```text
RustFS = stockage
```

---

## AWS CLI

AWS CLI permet de communiquer avec RustFS, car RustFS utilise une API compatible S3.

Exemple :

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls
```

Dans ce projet, AWS CLI communique avec **RustFS en local** et non avec Amazon AWS.

---

## Scripts de synchronisation

Les scripts de synchronisation permettent d'envoyer automatiquement certains fichiers vers RustFS.

Par exemple :

```text
sync-opencode-log.sh
```

sert à synchroniser les logs OpenCode.

Le fonctionnement est :

```text
OpenCode
   ↓
création d'un fichier ou d'un log
   ↓
script de synchronisation
   ↓
RustFS
```

---

## Apache Spark

Apache Spark est le moteur de traitement des données.

Son rôle est différent de RustFS :

```text
RustFS = stocker les données
Spark  = traiter les données
```

Spark peut notamment :

- lire des données ;
- filtrer des données ;
- compter des lignes ;
- regrouper des informations ;
- exécuter des requêtes SQL ;
- lire et écrire des tables Iceberg.

Dans ce projet, Spark fonctionne localement.

Il n'est pas nécessaire de le laisser actif en permanence : il est lancé lorsqu'un traitement est demandé depuis le dashboard.

---

## PySpark

PySpark permet d'utiliser Apache Spark avec Python.

```text
Python
   ↓
PySpark
   ↓
Apache Spark
```

---

## Apache Iceberg

Apache Iceberg sert à organiser les données du Data Lake sous forme de tables.

Il ne remplace ni RustFS ni Spark.

```text
RustFS  = stockage
Spark   = traitement
Iceberg = organisation des tables
```

Une table Iceberg peut être composée de plusieurs fichiers Parquet tout en étant manipulée comme une seule table.

Exemple de table :

```text
rustfs.opencode.logs
```

avec des colonnes comme :

```text
timestamp
session_id
type
content
source_file
```

---

## Parquet

Parquet est un format de fichier utilisé pour stocker efficacement les données.

Il est adapté aux traitements Big Data car il est :

- compact ;
- compressé ;
- rapide à lire ;
- adapté aux analyses.

Les données d'une table Iceberg sont principalement stockées dans des fichiers Parquet.

---

## Métadonnées et snapshots Iceberg

Iceberg conserve également des fichiers de métadonnées.

Ils servent à savoir :

- quels fichiers appartiennent à une table ;
- quelles colonnes existent ;
- quel est l'état actuel de la table ;
- quels anciens états sont disponibles.

Les **snapshots** représentent les différents états de la table au fil du temps.

Exemple :

```text
Snapshot 1
10 lignes

Snapshot 2
20 lignes

Snapshot 3
30 lignes
```

Cela permet de conserver un historique de la table.

---

# 2. Dashboard Streamlit

Streamlit permet d'afficher l'état de l'infrastructure dans une interface web.

Adresse :

```text
http://localhost:8501
```

Le dashboard contient plusieurs pages :

| Page | Utilité |
|---|---|
| 🏠 Vue générale | État global de l'infrastructure |
| 📦 Stockage S3 | Informations sur RustFS |
| 🧊 Iceberg | Données et snapshots Iceberg |
| ⚡ Spark | Résultats des traitements Spark |
| 🤖 OpenCode | Logs et activité OpenCode |

---

# 3. Cache du dashboard

Pour éviter de ralentir Streamlit, le dashboard ne lance pas directement de gros traitements à chaque affichage.

Des scripts séparés calculent les informations puis les enregistrent dans un cache local.

Le cache est stocké dans :

```text
~/.local/state/bigdata/dashboard_cache/
```

Le principe est :

```text
RustFS / Spark
      ↓
calcul des statistiques
      ↓
cache local
      ↓
Streamlit
```

Cela permet au dashboard de rester rapide même lorsque RustFS ou Spark ont besoin de plus de temps pour analyser les données.

---

# 4. `rustfs_dashboard_export.py`

Ce script analyse RustFS en arrière-plan.

Il calcule notamment :

- le nombre d'objets ;
- le volume total ;
- le nombre de logs ;
- le nombre de fichiers liés à Iceberg ;
- les types de fichiers présents ;
- les fichiers les plus volumineux ;
- l'activité du stockage.

Les résultats sont ensuite enregistrés dans le cache du dashboard.

Le bouton :

```text
📦 Actualiser RustFS
```

permet de relancer cet inventaire.

---

# 5. `spark_dashboard_export.py`

Ce script lance Spark en dehors de Streamlit.

Il permet notamment de récupérer :

- le nombre de lignes d'une table Iceberg ;
- les snapshots ;
- les statistiques par type ;
- l'activité dans le temps ;
- un aperçu des données.

Le résultat est ensuite enregistré dans le cache local.

Le bouton :

```text
⚡ Actualiser Spark / Iceberg
```

permet de lancer ce traitement.

---

# 6. Documentation Docsify

Docsify permet d'afficher la documentation Markdown du projet sous forme de site web.

Son rôle est différent de Streamlit :

```text
Streamlit = supervision de l'infrastructure et des données
Docsify   = documentation du projet
```

La documentation se trouve dans :

```text
~/BigData/docs/
```

avec les fichiers principaux :

```text
docs/
├── index.html
├── README.md
├── _sidebar.md
└── .nojekyll
```

- `index.html` charge Docsify ;
- `README.md` contient la documentation affichée ;
- `_sidebar.md` contient le menu de navigation ;
- `.nojekyll` permet notamment de faciliter une éventuelle publication avec GitHub Pages.

Docsify est chargé depuis un CDN dans `index.html`.

Il n'est donc pas nécessaire d'installer Docsify globalement avec npm.

Le site de documentation est servi localement avec Python :

```bash
python3 -m http.server 3000 --directory docs
```

Adresse :

```text
http://localhost:3000
```

Cette commande est maintenant intégrée automatiquement dans `start-all.sh`.

---

# 7. Environnement Python

Le projet utilise un environnement virtuel Python :

```text
~/BigData/.venv
```

Il contient les bibliothèques nécessaires au projet, par exemple :

```text
pyspark
streamlit
boto3
pandas
```

Pour l'activer manuellement :

```bash
cd ~/BigData
source .venv/bin/activate
```

---

# 8. Démarrage complet du projet

Le script principal est :

```text
start-all.sh
```

Il permet de démarrer toute l'infrastructure avec une seule commande :

```bash
cd ~/BigData
./start-all.sh
```

Il démarre notamment :

1. l'environnement Python ;
2. RustFS ;
3. OpenCode Serve ;
4. la synchronisation des logs ;
5. la synchronisation des fichiers vers S3 ;
6. le dashboard Streamlit ;
7. la documentation Docsify ;
8. l'inventaire RustFS en arrière-plan.

Une fois le démarrage terminé :

```text
Dashboard Streamlit :
http://localhost:8501

Documentation Docsify :
http://localhost:3000

RustFS :
http://localhost:9001

API S3 RustFS :
http://localhost:9000
```

Spark reste lancé à la demande depuis le dashboard.

---

# 9. Arrêt complet du projet

Le script :

```text
stop-all.sh
```

permet d'arrêter l'infrastructure.

Utilisation :

```bash
cd ~/BigData
./stop-all.sh
```

Il arrête notamment :

- Streamlit ;
- Docsify ;
- OpenCode ;
- les scripts de synchronisation ;
- les traitements Spark éventuels ;
- l'inventaire RustFS ;
- les services Docker/RustFS prévus par le script.

Docsify est arrêté grâce au processus du serveur Python utilisant le port `3000`.

---

# 10. Vérification de l'état

Le script :

```text
status-all.sh
```

permet de vérifier l'état des différents services.

Utilisation :

```bash
cd ~/BigData
./status-all.sh
```

Spark peut être inactif sans que cela représente une erreur : il est lancé uniquement lorsqu'un traitement est demandé.

---

# 11. Fonctionnement complet d'une donnée

Le parcours d'une donnée peut être résumé ainsi :

```text
1. OpenCode crée ou modifie une donnée
                ↓
2. La donnée est présente dans ~/BigData
                ↓
3. Un script de synchronisation peut l'envoyer vers RustFS
                ↓
4. RustFS stocke la donnée
                ↓
5. Spark peut lire et traiter la donnée
                ↓
6. Iceberg organise les données sous forme de tables
                ↓
7. Les données sont stockées en Parquet
                ↓
8. Iceberg conserve les métadonnées et snapshots
                ↓
9. Les scripts d'export calculent des statistiques
                ↓
10. Streamlit affiche les résultats dans le dashboard
```

Docsify fonctionne en parallèle :

```text
Documentation Markdown
        ↓
      Docsify
        ↓
Documentation web
```

Docsify ne participe donc pas au traitement des données.

---

# 12. Résumé du rôle de chaque technologie

| Technologie | Rôle |
|---|---|
| OpenCode | Produit et modifie des fichiers et des logs |
| Docker | Exécute RustFS dans un conteneur |
| Docker Compose | Configure et démarre RustFS |
| RustFS | Stocke les données en S3 |
| AWS CLI | Communique avec RustFS |
| Scripts de synchronisation | Envoient automatiquement les fichiers |
| Apache Spark | Traite et analyse les données |
| PySpark | Permet d'utiliser Spark avec Python |
| Apache Iceberg | Organise les données sous forme de tables |
| Parquet | Stocke efficacement les données |
| Snapshots | Conservent l'historique d'une table |
| Boto3 | Permet à Python de communiquer avec RustFS |
| Cache local | Évite de recalculer les statistiques à chaque page |
| Streamlit | Affiche le dashboard de supervision |
| Docsify | Affiche la documentation Markdown sous forme de site web |
| `start-all.sh` | Démarre l'ensemble de l'infrastructure |
| `stop-all.sh` | Arrête l'ensemble de l'infrastructure |
| `status-all.sh` | Vérifie l'état de l'infrastructure |

---

# 13. Commandes utiles

## Démarrer toute l'infrastructure

```bash
cd ~/BigData
./start-all.sh
```

## Arrêter toute l'infrastructure

```bash
cd ~/BigData
./stop-all.sh
```

## Vérifier les services

```bash
cd ~/BigData
./status-all.sh
```

## Lancer uniquement la documentation manuellement

```bash
cd ~/BigData
python3 -m http.server 3000 --directory docs
```

Puis ouvrir :

```text
http://localhost:3000
```

## Afficher les buckets RustFS

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls
```

## Afficher le contenu du bucket principal

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls s3://opencode-data/
```

---

# 14. Remarque sur Spark

Spark télécharge certaines dépendances nécessaires à son fonctionnement lors du premier lancement.

Ces fichiers peuvent être enregistrés dans un cache local.

Après un nettoyage du cache, le premier démarrage de Spark peut être plus long car les dépendances doivent être téléchargées à nouveau.

---

# 15. Ports utilisés

| Service | Port | Adresse |
|---|---:|---|
| Docsify | 3000 | `http://localhost:3000` |
| Streamlit | 8501 | `http://localhost:8501` |
| RustFS API S3 | 9000 | `http://localhost:9000` |
| RustFS interface | 9001 | `http://localhost:9001` |

---

# 16. Architecture finale

```text
                         OpenCode
                            │
                            ▼
                       ~/BigData
                            │
                     synchronisation
                            │
                            ▼
                         RustFS
                            │
                            ▼
                     Apache Spark
                            │
                            ▼
                    Apache Iceberg
                            │
               Parquet + métadonnées
                            │
                            ▼
                         RustFS
                            │
                            ▼
                       Cache local
                            │
                            ▼
                        Streamlit
                            │
                            ▼
                        Dashboard


En parallèle :

README.md / docs/
        │
        ▼
      Docsify
        │
        ▼
Documentation web
http://localhost:3000
```

---

# Conclusion

Ce projet met en place un **mini Data Lake local** permettant de reproduire les principales étapes d'une architecture Big Data.

Le fonctionnement peut être résumé simplement :

```text
OpenCode produit les données.

RustFS les stocke.

Spark les traite.

Iceberg les organise.

Parquet les contient.

Le cache conserve les statistiques.

Streamlit les affiche.

Docsify présente la documentation du projet.
```

L'infrastructure sépare ainsi clairement la production, le stockage, le traitement, l'organisation, la visualisation et la documentation des données.
