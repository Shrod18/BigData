# Projet BigData — Data Lake local

## Présentation

Ce projet met en place une petite infrastructure **Big Data / Data Lake en local**.

L'objectif est de reproduire simplement une architecture de données complète :

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

Chaque outil possède un rôle précis :

- **OpenCode** produit ou modifie les fichiers du projet.
- **RustFS** stocke les fichiers dans un espace compatible S3.
- **Apache Spark** traite et analyse les données.
- **Apache Iceberg** organise les données sous forme de tables.
- **Parquet** est utilisé pour stocker efficacement les données des tables Iceberg.
- **Streamlit** affiche les informations dans un dashboard web.
- **Docsify** transforme la documentation Markdown du projet en site web consultable.
- Des **scripts de synchronisation** permettent d'envoyer automatiquement certains fichiers et logs vers RustFS.

---

# 1. Architecture générale

```text
                         UTILISATEUR
                              │
                              ▼
                          OpenCode
                              │
                    crée / modifie des fichiers
                              │
                              ▼
                         ~/BigData
                              │
                       synchronisation
                              │
                              ▼
                           RustFS
                        Stockage S3
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
           fichiers / logs            Apache Spark
                                           │
                                           ▼
                                    Apache Iceberg
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                           Parquet      Metadata     Snapshots
                              │            │            │
                              └────────────┴────────────┘
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
```

---

# 2. Rôle de chaque composant

## OpenCode

OpenCode est utilisé comme assistant de développement.

Il peut notamment :

- lire les fichiers du projet ;
- créer ou modifier du code ;
- aider à corriger des erreurs ;
- produire des fichiers et des logs.

Dans cette infrastructure, OpenCode est donc aussi considéré comme une **source de données**.

---

## Dossier `~/BigData`

Le dossier principal du projet est :

```bash
~/BigData
```

Il contient les scripts, le dashboard et la configuration du projet.

Exemple :

```text
BigData/
├── dashboard.py
├── spark_dashboard_export.py
├── rustfs_dashboard_export.py
├── sync-opencode-log.sh
├── sync-opencode-s3.sh
├── docker-compose.yml
├── start-all.sh
├── stop-all.sh
├── status-all.sh
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

- l'image RustFS utilisée ;
- les ports ;
- le volume de stockage ;
- la configuration du conteneur.

---

## RustFS

RustFS est le système de stockage principal.

Il est compatible avec le protocole **Amazon S3**.

Dans ce projet, le bucket principal est :

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

Le fonctionnement est simple :

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
- effectuer des requêtes SQL ;
- lire et écrire des tables Iceberg.

Dans ce projet, Spark fonctionne localement sur la machine.

Il n'est pas nécessaire de le laisser actif en permanence : il est lancé lorsqu'un traitement est demandé.

---

## PySpark

PySpark permet d'utiliser Apache Spark avec Python.

Il sert d'intermédiaire entre les scripts Python et Spark.

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

Dans le projet, une table peut par exemple être appelée :

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

# 3. Dashboard Streamlit

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

# 4. Cache du dashboard

Pour éviter de ralentir Streamlit, le dashboard ne lance pas directement de gros traitements à chaque affichage.

Des scripts séparés calculent les informations puis les enregistrent dans un cache local.

Le cache est stocké dans :

```text
~/.local/state/bigdata/dashboard_cache/
```

Le fonctionnement est donc :

```text
RustFS / Spark
      ↓
calcul des statistiques
      ↓
cache local
      ↓
Streamlit
```

Cela permet au dashboard de s'afficher rapidement.

---

# 5. Script `rustfs_dashboard_export.py`

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

# 6. Script `spark_dashboard_export.py`

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

# 8. Démarrage du projet

Le script principal est :

```text
start-all.sh
```

Il permet de démarrer l'infrastructure avec une seule commande :

```bash
cd ~/BigData
./start-all.sh
```

Il démarre notamment :

- l'environnement Python ;
- RustFS ;
- OpenCode Serve ;
- les scripts de synchronisation ;
- Streamlit ;
- l'inventaire RustFS en arrière-plan.

Une fois démarré :

```text
Dashboard :
http://localhost:8501

RustFS :
http://localhost:9001
```

---

# 9. Arrêt du projet

Pour arrêter l'infrastructure :

```bash
cd ~/BigData
./stop-all.sh
```

Ce script arrête notamment :

- Streamlit ;
- OpenCode ;
- les scripts de synchronisation ;
- les traitements en arrière-plan ;
- RustFS.

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

Exemple d'état :

```text
RustFS      : actif
Streamlit   : actif
OpenCode    : actif
Spark       : inactif
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
8. Iceberg conserve également les métadonnées et snapshots
                ↓
9. Les scripts d'export calculent des statistiques
                ↓
10. Streamlit affiche les résultats dans le dashboard
```

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
| `start-all.sh` | Démarre l'infrastructure |
| `stop-all.sh` | Arrête l'infrastructure |
| `status-all.sh` | Vérifie l'état de l'infrastructure |

---

# 13. Documentation avec Docsify

Docsify est utilisé pour présenter la documentation du projet sous forme de site web.

Contrairement à Streamlit, Docsify ne sert pas à afficher les données du Data Lake.

Son rôle est uniquement de présenter la **documentation technique et fonctionnelle du projet**.

On peut donc distinguer :

```text
Streamlit = supervision des données et de l'infrastructure
Docsify   = documentation du projet
```

Docsify lit directement des fichiers Markdown et les affiche dans une interface web.

Le principe est :

```text
README.md / fichiers Markdown
            ↓
          Docsify
            ↓
   documentation web
```

## Organisation conseillée

Une organisation simple du dépôt Git peut être :

```text
BigData/
├── README.md
├── docs/
│   ├── index.html
│   ├── README.md
│   ├── _sidebar.md
│   └── .nojekyll
├── dashboard.py
├── spark_dashboard_export.py
├── rustfs_dashboard_export.py
├── docker-compose.yml
├── start-all.sh
├── stop-all.sh
└── status-all.sh
```

Le fichier principal de documentation peut être placé dans :

```text
docs/README.md
```

Le fichier :

```text
docs/index.html
```

charge Docsify et indique à Docsify où trouver les fichiers Markdown.

Exemple minimal :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentation BigData</title>
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/vue.css">
</head>

<body>
  <div id="app">Chargement...</div>

  <script>
    window.$docsify = {
      name: 'Projet BigData',
      repo: '',
      loadSidebar: true,
      subMaxLevel: 2
    }
  </script>

  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
</body>
</html>
```

Le fichier :

```text
docs/_sidebar.md
```

peut servir de menu de navigation.

Exemple :

```markdown
- [Accueil](README.md)
- [Architecture](README.md#1-architecture-générale)
- [RustFS](README.md#rustfs)
- [Apache Spark](README.md#apache-spark)
- [Apache Iceberg](README.md#apache-iceberg)
- [Dashboard Streamlit](README.md#3-dashboard-streamlit)
- [Commandes utiles](README.md#14-commandes-utiles)
```

Le fichier vide :

```text
docs/.nojekyll
```

est utile si la documentation est ensuite publiée avec GitHub Pages.

## Lancer Docsify en local

Si Docsify CLI est disponible :

```bash
docsify serve docs
```

ou avec `npx` :

```bash
npx docsify-cli serve docs
```

La documentation est alors généralement accessible sur :

```text
http://localhost:3000
```

## Place de Docsify dans le projet

Docsify n'intervient pas dans le traitement des données.

L'architecture fonctionnelle reste :

```text
OpenCode
   ↓
RustFS
   ↓
Apache Spark
   ↓
Apache Iceberg
   ↓
Streamlit
```

Docsify se place à côté de cette architecture :

```text
Projet Git
   │
   ├── Code et infrastructure
   │       ↓
   │   Streamlit
   │
   └── Documentation Markdown
           ↓
         Docsify
           ↓
    Documentation web
```

Ainsi, **Streamlit sert à visualiser le fonctionnement de l'infrastructure**, tandis que **Docsify sert à expliquer le projet**.

---

# 14. Commandes utiles

Démarrer le projet :

```bash
cd ~/BigData
./start-all.sh
```

Arrêter le projet :

```bash
cd ~/BigData
./stop-all.sh
```

Vérifier les services :

```bash
cd ~/BigData
./status-all.sh
```

Afficher les buckets RustFS :

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls
```

Afficher le contenu du bucket principal :

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls s3://opencode-data/
```

---

# 15. Remarque sur Spark

Spark télécharge certaines dépendances nécessaires à son fonctionnement lors du premier lancement.

Ces fichiers peuvent être mis en cache sur la machine.

Après un nettoyage du cache, le premier démarrage de Spark peut donc être plus long car les dépendances doivent être téléchargées à nouveau.

---

# 16. Conclusion

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

L'infrastructure sépare ainsi clairement la production, le stockage, le traitement, l'organisation et la visualisation des données.
