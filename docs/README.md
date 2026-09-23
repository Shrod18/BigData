# Projet BigData — Data Lake local

## Presentation

Ce projet met en place une petite infrastructure **Big Data / Data Lake en local**.

L'objectif est de reproduire simplement le fonctionnement d'une architecture de données complète :

- production de données ;
- ingestion de fichiers et de logs ;
- stockage compatible S3 ;
- traitement avec Apache Spark ;
- organisation des données avec Apache Iceberg ;
- conservation des données en Parquet ;
- supervision avec Streamlit ;
- documentation avec Docsify.

Le flux principal actuellement implémenté est :

```text
OpenCode
   ↓
Fichiers / logs
   ↓
Scripts de synchronisation
   ↓
RustFS / S3
   ↓
Apache Spark
   ↓
Transformations
   ↓
Apache Iceberg
   ↓
Iceberg Warehouse
   ↓
Parquet + Metadata + Snapshots
   ↓
Cache local
   ↓
Streamlit
   ↓
Dashboard / BI
```

La documentation fonctionne en parallèle :

```text
README.md
   ↓
Docsify
   ↓
Documentation web
```

Docsify ne participe pas au traitement des données. Il sert uniquement à présenter la documentation du projet.

---

<a id="infrastructure"></a>

# 1. Infrastructure

## OpenCode

OpenCode est utilisé comme assistant de développement.

Il permet notamment de :

- lire les fichiers du projet ;
- créer ou modifier du code ;
- aider à corriger des erreurs ;
- produire des fichiers et des logs.

Dans l'infrastructure, OpenCode peut également être considéré comme une **source de données**.

---

## Dossier BigData

Le dossier principal du projet est :

```bash
~/BigData
```

Il regroupe les scripts, la configuration, le dashboard et la documentation.

Structure simplifiée :

```text
BigData/
├── README.md
├── dashboard.py
├── spark_iceberg.py
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

Docker permet d'exécuter une application dans un **conteneur**, c'est-à-dire un environnement isolé qui regroupe l'application et ce dont elle a besoin pour fonctionner.

Dans ce projet, Docker sert principalement à lancer **RustFS** de manière isolée, reproductible et simple à démarrer ou arrêter.

Le fichier :

```text
docker-compose.yml
```

contient la configuration nécessaire au démarrage du service.

Le service RustFS utilise notamment :

| Élément | Valeur |
|---|---|
| Image | `rustfs/rustfs:latest` |
| Volume | `rustfs-data` monté dans `/data` |
| API S3 | `localhost:9000` |
| Console web | `localhost:9001` |

Commandes utiles :

```bash
docker compose up -d
docker compose ps
docker compose logs -f rustfs
docker compose down
```

Le volume n'est pas supprimé par `docker compose down`.

Les données RustFS restent donc disponibles lors du prochain démarrage.

---

## RustFS

RustFS est le système de stockage principal du projet.

Il fournit une API compatible avec **Amazon S3**. S3 est un modèle de stockage objet : au lieu d'organiser les données comme un disque classique, les fichiers sont enregistrés sous forme d'objets dans des **buckets**. Ici, RustFS reproduit ce fonctionnement en local.

Le bucket principal est :

```text
s3://opencode-data
```

RustFS peut stocker différents types de données :

- fichiers du projet ;
- logs OpenCode ;
- fichiers JSON ;
- fichiers Parquet ;
- métadonnées Iceberg ;
- données produites par Spark.

Adresses utilisées :

```text
API S3 :
http://localhost:9000

Interface RustFS :
http://localhost:9001
```

En résumé :

```text
RustFS = stockage objet compatible S3
```

### Organisation des objets

Le bucket utilisé par le projet est `opencode-data`.

Les préfixes principaux sont :

| Préfixe | Contenu | Catégorie |
|---|---|---|
| `logs/` | Logs OpenCode synchronisés | Logs OpenCode |
| `spark-warehouse/` | Données et métadonnées Iceberg | Iceberg / Spark |
| autres chemins | Fichiers du projet | Projet / fichiers |

RustFS conserve les objets dans son volume Docker et les expose par son API compatible S3.

### Accès S3

Configuration locale utilisée :

```text
Endpoint : http://127.0.0.1:9000
Région   : us-east-1
Bucket   : opencode-data
```

Exemples :

```bash
aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls

aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls s3://opencode-data/

aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls s3://opencode-data/logs/
```

L'option `--endpoint-url` est importante : sans elle, AWS CLI tente de contacter AWS au lieu de RustFS.

---

## AWS CLI

AWS CLI est un outil en ligne de commande permettant de manipuler des services compatibles AWS, notamment S3.

Dans ce projet, il permet de communiquer avec RustFS grâce à son API compatible S3.

Exemple :

```bash
aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls
```

Dans ce projet, cette commande communique avec **RustFS en local** et non avec Amazon AWS.

---

## Synchronisation

Des scripts permettent d'envoyer automatiquement certains fichiers vers RustFS.

Par exemple :

```text
sync-opencode-log.sh
```

sert à synchroniser les logs OpenCode.

Le principe général est :

```text
OpenCode / fichiers locaux
          ↓
script de synchronisation
          ↓
       RustFS / S3
```

Cette étape correspond au chargement des données brutes dans le stockage S3.

---

## Apache Spark

Apache Spark est le moteur de traitement des données. Un moteur de traitement permet de lire des données, d'appliquer des opérations dessus puis de produire un résultat exploitable.

Dans ce projet, Spark exécute les transformations nécessaires avant l'écriture ou l'analyse des données Iceberg.

Son rôle est différent de RustFS :

```text
RustFS = stockage
Spark  = traitement
```

Spark peut notamment :

- lire des données ;
- nettoyer les données ;
- filtrer des informations ;
- sélectionner des colonnes ;
- compter des lignes ;
- regrouper des données ;
- exécuter des requêtes SQL ;
- lire et écrire des tables Iceberg.

Dans ce projet, Spark fonctionne localement sur la machine.

Il n'est pas lancé en permanence.

Il est utilisé lorsqu'un traitement ou une actualisation des données Spark / Iceberg est demandé.

### Configuration locale

```text
master                 local[*]
Spark UI du test       http://localhost:4040
Spark UI de l'export   désactivée
shuffle.partitions     4 pour l'export du dashboard
```

Dépendances principales utilisées :

```text
org.apache.iceberg:iceberg-spark-runtime-4.1_2.13:1.11.0
org.apache.hadoop:hadoop-aws:3.4.2
```

Lors de la première exécution, Spark peut télécharger ces JAR depuis Maven.

### Lancer un test Spark complet

```bash
cd ~/BigData
source .venv/bin/activate
python spark_iceberg.py
```

Le script peut créer le namespace, créer la table, insérer une ligne, lire les données et afficher les snapshots.

---

## PySpark

PySpark est l'interface Python d'Apache Spark. Il permet donc d'écrire les traitements Spark directement en Python plutôt qu'en Scala ou en Java.

```text
Python
   ↓
PySpark
   ↓
Apache Spark
```

Les scripts Python du projet peuvent ainsi lancer des traitements Spark sans utiliser directement Scala ou Java.

---

## Apache Iceberg

Apache Iceberg est un **format de table pour Data Lake**. Il ajoute une structure de table au-dessus de fichiers stockés dans S3 et permet notamment de gérer le schéma, les versions, les snapshots et les écritures transactionnelles.

Dans ce projet, Iceberg organise les données du Data Lake sous forme de tables.

Il ne remplace ni RustFS ni Spark.

```text
RustFS  = stockage
Spark   = traitement
Iceberg = organisation des tables
```

Une table Iceberg peut être composée de plusieurs fichiers physiques tout en étant manipulée comme une seule table.

Exemple de table utilisée dans le projet :

```text
rustfs.opencode.logs
```

Schéma :

```text
timestamp
session_id
type
content
source_file
```

### Catalogue et entrepôt

Spark déclare un catalogue Iceberg nommé `rustfs` :

```text
Catalogue : rustfs
Type      : HadoopCatalog
Entrepôt  : s3a://opencode-data/spark-warehouse
Namespace : rustfs.opencode
Table     : rustfs.opencode.logs
```

Le chemin `s3a://` permet à Hadoop et Spark d'utiliser le connecteur S3A.

Les fichiers de données, les manifests et les métadonnées sont stockés dans RustFS.

Aucun serveur Iceberg séparé n'est nécessaire.

### Schéma de la table

| Colonne | Type | Utilisation |
|---|---|---|
| `timestamp` | `TIMESTAMP` | Date et heure de l'événement |
| `session_id` | `STRING` | Identifiant de session |
| `type` | `STRING` | Type de contenu ou d'événement |
| `content` | `STRING` | Contenu du log |
| `source_file` | `STRING` | Fichier d'origine |

Exemple de création SQL :

```sql
CREATE NAMESPACE IF NOT EXISTS rustfs.opencode;

CREATE TABLE IF NOT EXISTS rustfs.opencode.logs (
    timestamp TIMESTAMP,
    session_id STRING,
    type STRING,
    content STRING,
    source_file STRING
) USING iceberg;
```

Lecture :

```sql
SELECT *
FROM rustfs.opencode.logs
ORDER BY timestamp DESC;
```

Historique :

```sql
SELECT committed_at, snapshot_id, operation
FROM rustfs.opencode.logs.snapshots
ORDER BY committed_at DESC;
```

---

## Parquet

Parquet est un format de fichier **colonnaire** : les valeurs d'une même colonne sont stockées ensemble. Cette organisation est particulièrement adaptée aux analyses, car Spark peut lire uniquement les colonnes nécessaires sans parcourir toutes les données.

Il est donc utilisé pour stocker efficacement les données des tables Iceberg.

Il est notamment :

- compact ;
- compressé ;
- rapide à lire ;
- adapté aux traitements analytiques.

Les données d'une table Iceberg sont principalement stockées dans des fichiers Parquet.

---

## Metadata et snapshots Iceberg

Iceberg conserve également des **métadonnées**, c'est-à-dire des informations qui décrivent la table : son schéma, ses fichiers, ses versions et son état courant.

Un **snapshot** correspond à un état précis de la table à un instant donné. Lorsqu'une écriture est validée, Iceberg peut créer un nouveau snapshot sans remplacer brutalement l'état précédent.

Elles permettent notamment de savoir :

- quels fichiers appartiennent à la table ;
- quelles colonnes existent ;
- quel est l'état actuel de la table ;
- quels anciens états sont disponibles.

Les **snapshots** représentent différents états de la table au fil du temps.

```text
Snapshot 1
10 lignes

Snapshot 2
20 lignes

Snapshot 3
30 lignes
```

Chaque écriture Iceberg produit un nouvel état cohérent de la table.

Les snapshots permettent donc de suivre l'historique des opérations.

---

## Transactions ACID

Apache Iceberg apporte des garanties transactionnelles de type **ACID** au niveau des tables.

Une transaction correspond à une opération logique qui doit être appliquée de manière fiable. Les propriétés ACID évitent par exemple qu'une écriture partielle laisse la table dans un état incohérent.

ACID signifie :

- **Atomicité** : une opération est appliquée complètement ou pas du tout ;
- **Cohérence** : la table reste dans un état valide ;
- **Isolation** : les opérations concurrentes ne doivent pas produire un état incohérent ;
- **Durabilité** : une écriture validée reste conservée.

Le principe est :

```text
Apache Spark
     ↓
Apache Iceberg
     ↓
Transactions ACID
     ↓
Snapshots + Metadata
     ↓
Iceberg Warehouse / S3
```

---

<a id="dashboard-streamlit"></a>

# 2. Dashboard Streamlit

Streamlit permet d'afficher l'état du projet dans une interface web.

Adresse :

```text
http://localhost:8501
```

Le dashboard permet notamment de consulter :

| Page | Utilité |
|---|---|
| Vue générale | État global de l'infrastructure |
| Stockage S3 | Informations sur RustFS |
| Iceberg | Données et snapshots Iceberg |
| Spark | Résultats des traitements Spark |
| OpenCode | Logs et activité OpenCode |

Streamlit sert principalement à la **supervision** et à la **visualisation**.

---

<a id="cache-du-dashboard"></a>

# 3. Cache du dashboard

Un **cache** conserve temporairement un résultat déjà calculé afin d'éviter de refaire le même traitement à chaque affichage.

Le dashboard ne lance donc pas directement tous les traitements lourds à chaque ouverture ou changement de page.

Les informations calculées par RustFS et Spark sont enregistrées dans un cache local :

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

Cela permet au dashboard de rester réactif même lorsque l'analyse RustFS ou Spark prend du temps.

### Fichiers générés

| Fichier | Producteur | Contenu |
|---|---|---|
| `rustfs_status.json` | Export RustFS | État du dernier inventaire |
| `rustfs_summary.json` | Export RustFS | Volumétrie, catégories et extensions |
| `rustfs_recent.csv` | Export RustFS | Objets récemment modifiés |
| `rustfs_logs.csv` | Export RustFS | Logs OpenCode détectés |
| `spark_status.json` | Export Spark | État, erreur éventuelle et compteurs |
| `iceberg_rows.csv` | Export Spark | Aperçu des données Iceberg |
| `snapshots.csv` | Export Spark | Historique des snapshots |
| `spark_stats.csv` | Export Spark | Nombre de lignes par type |
| `spark_activity.csv` | Export Spark | Activité regroupée dans le temps |

---

<a id="export-rustfs"></a>

# 4. Export RustFS

Le script :

```text
rustfs_dashboard_export.py
```

analyse RustFS en arrière-plan.

Il peut notamment calculer :

- le nombre d'objets ;
- le volume total ;
- le nombre de logs ;
- le nombre d'objets liés à Iceberg ;
- les types de fichiers présents ;
- les fichiers les plus volumineux ;
- l'activité du stockage.

Les résultats sont enregistrés dans le cache local.

Dans le dashboard, le bouton :

```text
Actualiser RustFS
```

permet de relancer cet inventaire.

---

<a id="export-spark-et-iceberg"></a>

# 5. Export Spark et Iceberg

Le script :

```text
spark_dashboard_export.py
```

lance Spark en dehors de Streamlit.

Il permet notamment de récupérer :

- le nombre de lignes d'une table Iceberg ;
- les snapshots ;
- les statistiques par type ;
- l'activité dans le temps ;
- un aperçu des données.

Les résultats sont enregistrés dans le cache local.

Dans le dashboard, le bouton :

```text
Actualiser Spark / Iceberg
```

permet de lancer ce traitement.

---

<a id="documentation-docsify"></a>

# 6. Documentation Docsify

Docsify est un outil qui transforme des fichiers Markdown en documentation web navigable.

Dans ce projet, il permet d'afficher cette documentation sous forme de site sans modifier le fonctionnement de l'infrastructure Big Data.

Son rôle est différent de Streamlit :

```text
Streamlit = supervision de l'infrastructure
Docsify   = documentation du projet
```

La documentation Docsify est stockée dans :

```text
~/BigData/docs/
```

Structure :

```text
docs/
├── index.html
├── README.md
├── _sidebar.md
└── .nojekyll
```

`docs/README.md` contient toute la documentation.

`docs/_sidebar.md` contient le menu de navigation.

`docs/index.html` charge Docsify.

Docsify est chargé depuis un CDN, ce qui évite de devoir l'installer globalement avec npm.

La documentation est servie localement avec Python :

```bash
python3 -m http.server 3000 --directory docs
```

Adresse :

```text
http://localhost:3000
```

Cette commande est intégrée dans `start-all.sh`.

---

<a id="navigation-docsify"></a>

# 7. Navigation Docsify

La navigation utilise un seul fichier :

```text
docs/README.md
```

Les grandes sections disposent d'ancres HTML explicites.

Exemple :

```markdown
<a id="infrastructure"></a>

# 1. Infrastructure
```

Le `_sidebar.md` peut donc pointer vers ces ancres.

Configuration recommandée dans `docs/index.html` :

```javascript
window.$docsify = {
  name: 'Projet BigData',
  loadSidebar: true,
  subMaxLevel: 0,
  auto2top: true
}
```

`subMaxLevel: 0` évite que Docsify ajoute automatiquement tous les sous-titres dans le menu.

---

<a id="environnement-python"></a>

# 8. Environnement Python

Le projet utilise un environnement virtuel Python :

```text
~/BigData/.venv
```

Il contient notamment :

```text
pyspark
streamlit
boto3
pandas
```

Activation manuelle :

```bash
cd ~/BigData
source .venv/bin/activate
```

---

<a id="demarrage"></a>

# 9. Demarrage

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
- la synchronisation des logs ;
- la synchronisation des fichiers ;
- Streamlit ;
- Docsify ;
- l'inventaire RustFS en arrière-plan.

Une fois le projet démarré :

```text
Docsify :
http://localhost:3000

Streamlit :
http://localhost:8501

RustFS API :
http://localhost:9000

RustFS interface :
http://localhost:9001
```

Spark reste utilisé à la demande afin d'éviter de le laisser tourner inutilement en permanence.

---

<a id="arret"></a>

# 10. Arret

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
- les services prévus par le script.

---

<a id="verification"></a>

# 11. Verification

Le script :

```text
status-all.sh
```

permet de vérifier l'état des services.

Utilisation :

```bash
cd ~/BigData
./status-all.sh
```

Spark peut être inactif sans que cela représente une erreur.

Il est lancé uniquement lorsqu'un traitement est nécessaire.

---

<a id="commandes-utiles"></a>

# 12. Commandes utiles

## Demarrer le projet

```bash
cd ~/BigData
./start-all.sh
```

## Arreter le projet

```bash
cd ~/BigData
./stop-all.sh
```

## Verifier les services

```bash
cd ~/BigData
./status-all.sh
```

## Lancer uniquement Docsify

```bash
cd ~/BigData
python3 -m http.server 3000 --directory docs
```

## Afficher les buckets RustFS

```bash
aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls
```

## Afficher le contenu du bucket principal

```bash
aws --profile rustfs \
  --endpoint-url http://localhost:9000 \
  s3 ls s3://opencode-data/
```

## Activer l'environnement Python

```bash
cd ~/BigData
source .venv/bin/activate
```

---

<a id="ports"></a>

# 13. Ports

| Service | Port | Adresse |
|---|---:|---|
| Docsify | 3000 | `http://localhost:3000` |
| Streamlit | 8501 | `http://localhost:8501` |
| RustFS API S3 | 9000 | `http://localhost:9000` |
| RustFS interface | 9001 | `http://localhost:9001` |

---

<a id="architecture-etl"></a>

# 14. Architecture Extract, Transform et Load

Le projet peut être décrit simplement avec une logique de type **ETL**.

ETL signifie **Extract, Transform, Load** :
- **Extract** : récupérer les données depuis leur source ;
- **Transform** : nettoyer, filtrer, regrouper ou modifier les données ;
- **Load** : écrire le résultat dans la destination choisie.

Dans ce projet, les données brutes sont d'abord chargées dans RustFS/S3, puis Spark réalise les transformations avant l'écriture dans Iceberg.

```text
             EXTRACT
                │
                ▼
       OpenCode / fichiers
                │
                ▼
     scripts de synchronisation
                │
                ▼
          RustFS / S3
                │
                │
                ▼
            TRANSFORM
          Apache Spark
                │
                ▼
              LOAD
                │
                ▼
         Apache Iceberg
                │
                ▼
       Iceberg Warehouse
                │
       Parquet + Metadata
        + Snapshots ACID
                │
                ▼
         Streamlit / BI
```

## Extract

La partie **Extract** consiste à récupérer les données produites par les sources. L'objectif est de rendre ces données disponibles pour la suite du pipeline, sans encore réaliser les transformations analytiques principales.

Dans le projet :

```text
OpenCode
   ↓
fichiers / logs
   ↓
scripts de synchronisation
```

Les données sont ensuite envoyées dans RustFS.

---

## Inputs S3

Un **input** correspond à une donnée d'entrée du pipeline. Ici, les inputs sont principalement les fichiers et logs déposés dans le stockage S3.

Les données brutes sont chargées dans :

```text
s3://opencode-data/
```

RustFS constitue donc la couche de stockage S3 du projet.

```text
Fichiers / logs
      ↓
RustFS / S3
      ↓
Apache Spark
```

---

## Transform

La partie **Transform** correspond au traitement des données afin de les rendre propres, cohérentes et exploitables.

Dans ce projet, cette étape est réalisée par Apache Spark.

Spark peut notamment effectuer :

- nettoyage ;
- filtrage ;
- sélection de colonnes ;
- changement de format ;
- regroupement ;
- agrégation ;
- calcul de statistiques ;
- préparation des données avant leur écriture.

```text
RustFS / S3
     ↓
Apache Spark
     ↓
Transform
```

---

## Load

Le **Load** correspond à l'étape où les données transformées sont écrites dans leur destination finale ou analytique.

Dans ce projet, le Load correspond à l'écriture des données transformées dans Apache Iceberg.

```text
Apache Spark
     ↓
Load
     ↓
Apache Iceberg
     ↓
Iceberg Warehouse
```

Le warehouse est stocké dans :

```text
s3a://opencode-data/spark-warehouse
```

Il ne s'agit pas d'un serveur supplémentaire.

C'est une zone du bucket S3 utilisée par Iceberg.

---

## Iceberg Warehouse

Un **warehouse** est l'emplacement de stockage utilisé par Iceberg pour conserver les fichiers physiques de ses tables : données Parquet, métadonnées, manifests et snapshots.

Dans ce projet, le warehouse correspond à la zone `s3a://opencode-data/spark-warehouse` stockée dans RustFS.

Le warehouse contient notamment :

```text
Iceberg Warehouse
│
├── fichiers Parquet
├── metadata
├── manifests
└── snapshots
```

Il faut distinguer les rôles :

```text
Iceberg
→ organise et versionne les tables

RustFS / S3
→ stocke physiquement les fichiers

Spark
→ lit, transforme et écrit les données
```

---

## ACID

Les propriétés **ACID** garantissent qu'une modification de table est appliquée de manière fiable et cohérente, même en cas d'échec ou d'opérations concurrentes.

Iceberg apporte ces propriétés transactionnelles aux tables.

```text
Spark
  ↓
Iceberg
  ↓
Transactions ACID
  ↓
Snapshots + Metadata
  ↓
Warehouse S3
```

Cela permet notamment de conserver des états cohérents des tables et un historique des écritures.

---

## Restitution

La **restitution** correspond au moment où les résultats préparés sont présentés à l'utilisateur sous une forme lisible : indicateurs, tableaux ou graphiques.

Une fois les données organisées dans Iceberg, elles peuvent être lues et analysées par Spark.

Les résultats utiles au dashboard sont ensuite exportés vers un cache local.

```text
Iceberg Warehouse
       ↓
     Spark
       ↓
statistiques / agrégations
       ↓
   Cache local
       ↓
   Streamlit / BI
```

Dans l'architecture actuelle, aucune base de restitution supplémentaire n'est nécessaire.

---

<a id="architecture-finale"></a>

# 15. Architecture finale

```text
                         OpenCode
                            │
                            ▼
                    Fichiers / Logs
                            │
                            ▼
                 Scripts de synchronisation
                            │
                            ▼
                       RustFS / S3
                            │
                            ▼
                     Apache Spark
                            │
                      Transform
                            │
                            ▼
                    Apache Iceberg
                            │
                         Load
                            │
                            ▼
                  Iceberg Warehouse
                            │
            Parquet + Metadata + Manifests
                            │
                    Snapshots / ACID
                            │
                            ▼
                     Apache Spark
                            │
             statistiques / agrégations
                            │
                            ▼
                       Cache local
                            │
                            ▼
                        Streamlit
                            │
                            ▼
                     Dashboard / BI
```

La documentation fonctionne en parallèle :

```text
docs/README.md
      │
      ▼
    Docsify
      │
      ▼
Documentation web
http://localhost:3000
```

---

<a id="fonctionnement-global"></a>

# 16. Fonctionnement global

```text
1. OpenCode crée ou modifie une donnée
                ↓
2. La donnée est présente dans le projet
                ↓
3. Un script la synchronise vers RustFS
                ↓
4. RustFS la stocke dans S3
                ↓
5. Spark lit les données
                ↓
6. Spark les transforme
                ↓
7. Spark écrit les données dans Iceberg
                ↓
8. Iceberg organise les tables
                ↓
9. Le warehouse stocke Parquet et les métadonnées
                ↓
10. Iceberg conserve les snapshots et les transactions ACID
                ↓
11. Spark calcule les statistiques du dashboard
                ↓
12. Les résultats sont placés dans le cache local
                ↓
13. Streamlit affiche les résultats
```

Docsify reste indépendant du flux de données :

```text
Documentation Markdown
        ↓
      Docsify
        ↓
Documentation web
```

---

<a id="resume-des-technologies"></a>

# 17. Resume des technologies

| Technologie | Rôle |
|---|---|
| OpenCode | Produit et modifie des fichiers et des logs |
| Docker | Exécute RustFS dans un conteneur |
| Docker Compose | Configure et démarre RustFS |
| RustFS | Stocke les données via S3 |
| AWS CLI | Communique avec RustFS |
| Scripts de synchronisation | Chargent les fichiers dans S3 |
| Apache Spark | Lit, transforme et analyse les données |
| PySpark | Permet d'utiliser Spark avec Python |
| Apache Iceberg | Organise et versionne les tables |
| Iceberg Warehouse | Zone S3 contenant les tables Iceberg |
| Parquet | Stocke les données |
| Metadata / Manifests | Décrivent les tables Iceberg |
| Snapshots | Conservent l'historique des tables |
| ACID | Garantit la cohérence transactionnelle des tables |
| Boto3 | Permet à Python de communiquer avec RustFS |
| Cache local | Conserve les statistiques du dashboard |
| Streamlit | Affiche le dashboard / BI |
| Docsify | Affiche la documentation du projet |
| `start-all.sh` | Démarre l'infrastructure |
| `stop-all.sh` | Arrête l'infrastructure |
| `status-all.sh` | Vérifie l'état de l'infrastructure |

---

<a id="depannage"></a>

# 18. Depannage

## RustFS ne repond pas

```bash
docker compose ps
docker compose logs --tail=100 rustfs
curl -I http://127.0.0.1:9000
ss -ltn | grep -E ':9000|:9001'
```

---

## Bucket incorrect

```bash
aws --profile rustfs \
  --endpoint-url http://127.0.0.1:9000 \
  s3 ls

aws --profile rustfs \
  --endpoint-url http://127.0.0.1:9000 \
  s3 ls s3://opencode-data/
```

---

## Spark ne demarre pas

Consulter :

```bash
cat ~/.local/state/bigdata/spark-export.log
cat ~/.local/state/bigdata/dashboard_cache/spark_status.json
```

Les causes fréquentes sont :

- environnement `.venv` non disponible ;
- RustFS inaccessible ;
- dépendances Iceberg/Hadoop non téléchargées ;
- mauvaise configuration du warehouse.

---

## La table Iceberg est introuvable

Vérifier :

```text
Bucket    : opencode-data
Entrepôt  : s3a://opencode-data/spark-warehouse
Table     : rustfs.opencode.logs
```

---

## Le dashboard affiche d'anciennes donnees

Le dashboard lit le cache et ne recalcule pas systématiquement les données à chaque affichage.

Pour supprimer uniquement le cache :

```bash
rm -f ~/.local/state/bigdata/dashboard_cache/*.csv
rm -f ~/.local/state/bigdata/dashboard_cache/*.json
```

Cette opération ne supprime aucune donnée dans RustFS.

---

## Docsify n'affiche pas la derniere version

Mettre à jour :

```bash
cp ~/BigData/README.md ~/BigData/docs/README.md
```

Puis utiliser :

```text
Ctrl + F5
```

dans le navigateur.

---

# Conclusion

Ce projet met en place un **mini Data Lake local**.

Le fonctionnement peut être résumé simplement :

```text
OpenCode produit les données.

Les scripts les chargent dans RustFS / S3.

Spark les lit et les transforme.

Iceberg organise les données en tables.

Le warehouse conserve Parquet, metadata et snapshots.

Iceberg apporte les propriétés ACID.

Spark calcule les statistiques utiles à la restitution.

Le cache local conserve ces résultats.

Streamlit les affiche.

Docsify présente la documentation.
```

L'architecture mise en place reste volontairement simple :

```text
Sources
   ↓
S3
   ↓
Spark
   ↓
Transform
   ↓
Iceberg
   ↓
Warehouse
   ↓
Streamlit / BI
```
