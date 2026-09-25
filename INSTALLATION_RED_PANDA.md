# Mise en place de Redpanda dans BigData

## Architecture ajoutée

```text
OpenCode / logs
      ↓
redpanda_producer.py
      ↓
Redpanda
topic opencode.logs
      ↓
Spark Structured Streaming
      ↓
Transformation JSON
      ↓
Apache Iceberg
      ↓
rustfs.opencode.logs_stream
      ↓
RustFS / S3
```

Cette branche complète la voie batch déjà présente :

```text
Fichiers
   ↓
RustFS / S3
   ↓
Spark Batch
   ↓
Iceberg
```

## Installation

Les fichiers de ce pack doivent être copiés à la racine de `~/BigData`.

Puis :

```bash
cd ~/BigData

chmod +x \
  setup-redpanda.sh \
  start-redpanda.sh \
  stop-redpanda.sh \
  status-redpanda.sh \
  send-redpanda-test.sh

./setup-redpanda.sh
```

## Démarrage

RustFS doit être actif sur le port 9000.

Ensuite :

```bash
./start-redpanda.sh
```

Redpanda Console :

```text
http://localhost:8080
```

Kafka API :

```text
localhost:19092
```

Topic :

```text
opencode.logs
```

## Vérification

```bash
./status-redpanda.sh
```

Logs :

```bash
tail -f ~/.local/state/bigdata/redpanda-producer.log
```

et :

```bash
tail -f ~/.local/state/bigdata/spark-redpanda.log
```

## Envoyer un message de test

```bash
./send-redpanda-test.sh
```

Spark traite ensuite le message et l'écrit dans :

```text
rustfs.opencode.logs_stream
```

## Lire les messages du topic

```bash
docker exec redpanda-0 \
  rpk topic consume opencode.logs -n 5
```

## Arrêt

```bash
./stop-redpanda.sh
```

Les données de Redpanda restent dans le volume Docker.

Pour supprimer volontairement ce volume :

```bash
docker compose \
  -f docker-compose.redpanda.yml \
  down -v
```

## CI GitHub Actions

Le fichier `ci-redpanda.yml` contient la version mise à jour du workflow.

Pour l'utiliser :

```bash
cp ci-redpanda.yml .github/workflows/ci.yml
```

Puis :

```bash
git add .
git commit -m "Ajout de Redpanda et du streaming Spark"
git push
```
