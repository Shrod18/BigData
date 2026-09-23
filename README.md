# Projet BigData — Data Lake local

## Presentation

Ce projet met en place une petite infrastructure **Big Data / Data Lake en local**.

L'objectif est de reproduire simplement le fonctionnement d'une architecture de données complète : production, stockage, traitement, organisation, supervision et documentation.

Le flux principal est :

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

La documentation fonctionne en parallèle :

```text
README.md
   ↓
Docsify
   ↓
Documentation web
```

Docsify ne participe pas au traitement des données. Il sert uniquement à afficher cette documentation sous forme de site web.

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

Dans l'infrastructure, OpenCode peut donc aussi être considéré comme une **source de données**.

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

Docker permet d'exécuter certains composants du projet dans des conteneurs.

Dans ce projet, il sert principalement à lancer **RustFS**.

Le fichier :

```text
docker-compose.yml
```

contient la configuration nécessaire au démarrage du service.

Docker permet donc d'isoler RustFS du reste du système tout en conservant ses données dans un volume.

Le service est décrit dans `docker-compose.yml` :

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

Le volume n'est pas supprimé par `docker compose down`. Les données RustFS
restent donc disponibles lors du prochain démarrage.

---

## RustFS

RustFS est le système de stockage principal du projet.

Il fournit une API compatible avec **Amazon S3**.

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
RustFS = stockage
```

### Organisation des objets

Le bucket utilisé par le projet est `opencode-data`. Les préfixes principaux
sont :

| Préfixe | Contenu | Catégorie du dashboard |
|---|---|---|
| `logs/` | Logs OpenCode synchronisés | Logs OpenCode |
| `spark-warehouse/` | Données et métadonnées Iceberg | Iceberg / Spark |
| autres chemins | Fichiers du projet | Projet / fichiers |

Un préfixe S3 ressemble à un dossier, mais il s'agit en réalité d'une partie
de la clé de l'objet. RustFS conserve les objets dans son volume Docker et
les expose par son API compatible S3.

### Accès S3

Les scripts utilisent les paramètres locaux suivants :

```text
Endpoint : http://127.0.0.1:9000
Région   : us-east-1
Clé      : rustfsadmin
Secret   : rustfsadmin
Bucket   : opencode-data
```

Ces identifiants sont adaptés à un environnement local de démonstration.
Ils doivent être remplacés avant toute exposition du service sur un réseau.

Exemples de vérification :

```bash
aws --profile rustfs --endpoint-url http://localhost:9000 s3 ls
aws --profile rustfs --endpoint-url http://localhost:9000 s3 ls s3://opencode-data/
aws --profile rustfs --endpoint-url http://localhost:9000 s3 ls s3://opencode-data/logs/
```

L'option `--endpoint-url` est importante : sans elle, AWS CLI tente de
contacter AWS au lieu de RustFS.

---

## AWS CLI

AWS CLI permet de communiquer avec RustFS grâce à son API compatible S3.

Exemple :

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls
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
        RustFS
```

Cela évite d'envoyer manuellement chaque fichier vers le stockage S3.

---

## Apache Spark

Apache Spark est le moteur de traitement des données.

Son rôle est différent de RustFS :

```text
RustFS = stockage
Spark  = traitement
```

Spark peut notamment :

- lire des données ;
- filtrer des informations ;
- compter des lignes ;
- regrouper des données ;
- exécuter des requêtes SQL ;
- lire et écrire des tables Iceberg.

Dans ce projet, Spark fonctionne localement sur la machine.

Il n'est pas lancé en permanence. Il est utilisé lorsqu'un traitement ou une actualisation des données Spark / Iceberg est demandé.

### Configuration locale

```text
master                 local[*]
Spark UI du test       http://localhost:4040
Spark UI de l'export   désactivée
shuffle.partitions     4 pour l'export du dashboard
```

`local[*]` utilise les cœurs disponibles sur la machine. L'export du
dashboard désactive la Spark UI car il s'agit d'un traitement court exécuté
en arrière-plan. Le script interactif `spark_iceberg.py`, lui, conserve la UI
pour observer le traitement.

Les dépendances chargées par Spark sont :

```text
org.apache.iceberg:iceberg-spark-runtime-4.1_2.13:1.11.0
org.apache.hadoop:hadoop-aws:3.4.2
```

Lors de la première exécution, Spark peut télécharger ces JAR depuis Maven.

### Lancer un test Spark complet

Le script crée le namespace, crée la table, insère une ligne, lit les données
et affiche les snapshots :

```bash
cd ~/BigData
source .venv/bin/activate
python spark_iceberg.py
```

Le traitement du dashboard, lui, est lancé en arrière-plan depuis Streamlit
ou `start-all.sh`.

---

## PySpark

PySpark permet d'utiliser Apache Spark depuis Python.

Le principe est :

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

Apache Iceberg sert à organiser les données du Data Lake sous forme de tables.

Il ne remplace ni RustFS ni Spark.

```text
RustFS  = stockage
Spark   = traitement
Iceberg = organisation des tables
```

Une table Iceberg peut être composée de plusieurs fichiers physiques, tout en étant manipulée comme une seule table.

Exemple de table utilisée dans le projet :

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
Les fichiers de données, les manifests et les métadonnées sont stockés dans
RustFS : aucun serveur Iceberg séparé n'est nécessaire.

### Schéma de la table

| Colonne | Type | Utilisation |
|---|---|---|
| `timestamp` | `TIMESTAMP` | Date et heure de l'événement |
| `session_id` | `STRING` | Identifiant de session |
| `type` | `STRING` | Type de contenu ou d'événement |
| `content` | `STRING` | Contenu du log |
| `source_file` | `STRING` | Fichier d'origine |

Création SQL :

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

Lecture et historique :

```sql
SELECT * FROM rustfs.opencode.logs ORDER BY timestamp DESC;

SELECT committed_at, snapshot_id, operation
FROM rustfs.opencode.logs.snapshots
ORDER BY committed_at DESC;
```

---

## Parquet

Parquet est un format de fichier adapté au stockage et à l'analyse de données.

Il est notamment :

- compact ;
- compressé ;
- rapide à lire ;
- adapté aux traitements analytiques.

Les données d'une table Iceberg sont principalement stockées dans des fichiers Parquet.

---

## Metadata et snapshots Iceberg

Iceberg conserve également des métadonnées.

Elles permettent notamment de savoir :

- quels fichiers appartiennent à la table ;
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

Cela permet de conserver un historique des évolutions de la table.

Chaque écriture Iceberg produit un nouveau snapshot. Les snapshots permettent
donc de suivre l'historique des opérations et les métadonnées décrivent le
schéma, les manifests et les fichiers associés à chaque état.

---

<a id="dashboard-streamlit"></a>
# 2. Dashboard Streamlit

Streamlit permet d'afficher l'état du projet dans une interface web.

Adresse :

```text
http://localhost:8501
```

Le dashboard permet notamment de consulter :

| Page | Utilite |
|---|---|
| Vue generale | Etat global de l'infrastructure |
| Stockage S3 | Informations sur RustFS |
| Iceberg | Donnees et snapshots Iceberg |
| Spark | Resultats des traitements Spark |
| OpenCode | Logs et activite OpenCode |

Streamlit sert donc principalement à la **supervision** et à la **visualisation**.

---

<a id="cache-du-dashboard"></a>
# 3. Cache du dashboard

Le dashboard ne lance pas directement tous les traitements lourds à chaque affichage.

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

Le cache est écrit dans `~/.local/state/bigdata/dashboard_cache/` :

| Fichier | Producteur | Contenu |
|---|---|---|
| `rustfs_status.json` | Export RustFS | État du dernier inventaire |
| `rustfs_summary.json` | Export RustFS | Volumétrie, catégories et extensions |
| `rustfs_recent.csv` | Export RustFS | Objets récemment modifiés |
| `rustfs_logs.csv` | Export RustFS | Logs OpenCode détectés |
| `spark_status.json` | Export Spark | État, erreur éventuelle et compteurs |
| `iceberg_rows.csv` | Export Spark | Aperçu limité à 2 000 lignes |
| `snapshots.csv` | Export Spark | Historique des snapshots |
| `spark_stats.csv` | Export Spark | Nombre de lignes par type |
| `spark_activity.csv` | Export Spark | Activité regroupée par heure |

Les exports écrivent d'abord un fichier temporaire puis le remplacent. Le
dashboard peut ainsi lire un fichier complet pendant qu'un nouveau traitement
est en cours.

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

Les résultats sont ensuite enregistrés dans le cache local.

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

Docsify permet d'afficher cette documentation Markdown sous forme de site web.

Son rôle est différent de Streamlit :

```text
Streamlit = supervision de l'infrastructure
Docsify   = documentation du projet
```

La documentation Docsify est stockée dans :

```text
~/BigData/docs/
```

Structure utilisée :

```text
docs/
├── index.html
├── README.md
├── _sidebar.md
└── .nojekyll
```

Le fichier :

```text
docs/README.md
```

contient toute la documentation.

Le fichier :

```text
docs/_sidebar.md
```

contient le menu de navigation.

Le menu pointe vers les différentes sections de ce même README.

Il n'est donc pas nécessaire de créer plusieurs fichiers Markdown pour chaque page.

Le fichier :

```text
docs/index.html
```

charge Docsify.

Docsify est chargé depuis un CDN, ce qui évite d'avoir à l'installer globalement avec npm.

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

La navigation Docsify utilise un seul fichier :

```text
docs/README.md
```

Le fichier `_sidebar.md` contient des liens vers les différentes sections du README.

Exemple :

```markdown
# Projet BigData

- [Accueil](#)
- [Presentation](#presentation)
- [Infrastructure](#infrastructure)
- [Dashboard](#dashboard-streamlit)
- [Cache](#cache-du-dashboard)
- [Docsify](#documentation-docsify)
- [Demarrage](#demarrage)
- [Arret](#arret)
- [Commandes](#commandes-utiles)
- [Ports](#ports)
- [Architecture finale](#architecture-finale)
```

Les grandes sections numérotées utilisent des ancres HTML explicites placées
juste avant leur titre, par exemple :

```markdown
<a id="infrastructure"></a>
# 1. Infrastructure
```

Cette méthode évite les problèmes liés aux numéros dans les ancres générées
automatiquement. Les liens du menu restent relatifs, sous la forme `#ancre`,
afin que Docsify conserve la page courante et fasse défiler la documentation
vers la section demandée. Les sous-parties utilisent les ancres automatiques
de Docsify, par exemple `#rustfs` ou `#apache-spark`.

Dans `index.html`, la configuration peut utiliser :

```javascript
window.$docsify = {
  name: 'Projet BigData',
  loadSidebar: true,
  subMaxLevel: 0,
  auto2top: true
}
```

`subMaxLevel: 0` évite que Docsify ajoute automatiquement tous les sous-titres dans le menu latéral.

---

<a id="environnement-python"></a>
# 8. Environnement Python

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

Spark reste utilisé à la demande pour éviter de le laisser tourner inutilement en permanence.

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

Docsify est arrêté en libérant le serveur Python utilisant le port `3000`.

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
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls
```

## Afficher le contenu du bucket principal

```bash
aws --profile rustfs   --endpoint-url http://localhost:9000   s3 ls s3://opencode-data/
```

## Activer manuellement l'environnement Python

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

<a id="architecture-finale"></a>
# 14. Architecture finale

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
               Parquet + metadata
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
# 15. Fonctionnement global

Le parcours général d'une donnée est :

```text
1. OpenCode crée ou modifie une donnée
                ↓
2. La donnée est présente dans le projet
                ↓
3. Un script peut la synchroniser vers RustFS
                ↓
4. RustFS la stocke
                ↓
5. Spark peut la lire et la traiter
                ↓
6. Iceberg organise les données en tables
                ↓
7. Les données sont stockées en Parquet
                ↓
8. Iceberg conserve les metadata et snapshots
                ↓
9. Les scripts d'export calculent les statistiques
                ↓
10. Streamlit affiche les résultats
```

Docsify reste indépendant de ce flux :

```text
Documentation Markdown
        ↓
      Docsify
        ↓
Documentation web
```

---

<a id="resume-des-technologies"></a>
# 16. Resume des technologies

| Technologie | Role |
|---|---|
| OpenCode | Produit et modifie des fichiers et des logs |
| Docker | Execute RustFS dans un conteneur |
| Docker Compose | Configure et demarre RustFS |
| RustFS | Stocke les donnees en S3 |
| AWS CLI | Communique avec RustFS |
| Scripts de synchronisation | Envoient automatiquement les fichiers |
| Apache Spark | Traite et analyse les donnees |
| PySpark | Permet d'utiliser Spark avec Python |
| Apache Iceberg | Organise les donnees sous forme de tables |
| Parquet | Stocke efficacement les donnees |
| Snapshots | Conservent l'historique des tables |
| Boto3 | Permet a Python de communiquer avec RustFS |
| Cache local | Evite de recalculer les statistiques a chaque affichage |
| Streamlit | Affiche le dashboard |
| Docsify | Affiche la documentation du projet |
| `start-all.sh` | Demarre l'infrastructure |
| `stop-all.sh` | Arrete l'infrastructure |
| `status-all.sh` | Verifie l'etat de l'infrastructure |

---

<a id="depannage"></a>
# 17. Dépannage

## RustFS ne répond pas

Vérifier le conteneur et les ports :

```bash
docker compose ps
docker compose logs --tail=100 rustfs
curl -I http://127.0.0.1:9000
ss -ltn | grep -E ':9000|:9001'
```

Si RustFS vient d'être installé, démarrer l'infrastructure avec
`./start-all.sh`. Une erreur `Connection refused` indique généralement que
le conteneur n'est pas démarré ou que le port `9000` est déjà utilisé.

## Bucket ou identifiants incorrects

Tester l'accès avec le même endpoint que les scripts :

```bash
aws --profile rustfs --endpoint-url http://127.0.0.1:9000 s3 ls
aws --profile rustfs --endpoint-url http://127.0.0.1:9000 s3 ls s3://opencode-data/
```

Une erreur d'authentification vient souvent du profil AWS, tandis qu'une
erreur `NoSuchBucket` signifie que `opencode-data` n'existe pas encore.

## Spark ne démarre pas

Consulter le journal et l'état du dernier export :

```bash
cat ~/.local/state/bigdata/spark-export.log
cat ~/.local/state/bigdata/dashboard_cache/spark_status.json
```

Les causes fréquentes sont l'absence de l'environnement `.venv`, un accès
impossible à RustFS ou le téléchargement impossible des JAR Iceberg/Hadoop.
Le script doit être lancé avec le Python de l'environnement virtuel.

## La table Iceberg est introuvable

Vérifier successivement le bucket, l'entrepôt et le nom complet de la table :

```text
Bucket    opencode-data
Entrepôt  s3a://opencode-data/spark-warehouse
Table     rustfs.opencode.logs
```

Une différence entre `s3://` et `s3a://`, un mauvais endpoint ou un namespace
différent suffit à empêcher Spark de retrouver la table.

## Le dashboard affiche d'anciennes données

Le dashboard lit le cache et ne recalcule pas systématiquement les données à
chaque affichage. Relancer l'export depuis le dashboard ou supprimer uniquement
les fichiers du cache, puis relancer l'export :

```bash
rm -f ~/.local/state/bigdata/dashboard_cache/*.csv
rm -f ~/.local/state/bigdata/dashboard_cache/*.json
```

Cette commande ne supprime aucune donnée dans RustFS ; elle efface seulement
les résultats calculés localement.

---

# Conclusion

Ce projet met en place un **mini Data Lake local** permettant de reproduire les principales étapes d'une architecture Big Data.

Le rôle de chaque grande partie peut être résumé simplement :

```text
OpenCode produit les données.

RustFS les stocke.

Spark les traite.

Iceberg les organise.

Parquet les contient.

Le cache conserve les statistiques.

Streamlit les affiche.

Docsify présente la documentation.
```

L'infrastructure sépare ainsi clairement la production, le stockage, le traitement, l'organisation, la visualisation et la documentation.
