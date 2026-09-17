# AGENTS.md

## What this is

This repo contains only `docker-compose.yml`: it runs `rustfs/rustfs:latest`, an S3-compatible object store.

- S3 API on host port `9000`, console/UI on host port `9001`.
- Data is persisted in the named volume `rustfs-data` (mounted at `/data`), survives container rebuilds.
- Start it with `docker compose up -d`; check logs with `docker compose logs -f rustfs`.
- Compose project/volume names are prefixed with `bigdata_` (derived from the directory name).

## Gotchas

- The git repo has no commits yet (`main` is unborn); don't expect commit history.
- `docker-compose.yml:Zone.Identifier` is a leftover Windows download-sidecar (NTFS ADS marker); ignore it, do not treat it as a real file.