# IBERO Identity Access Migration - Merged Package

This package consolidates the latest uploaded files with the previous V2 package.

## What is active in this merged package
- `db/000_schema.sql`: active database schema (public tables)
- `dataset/*.csv`: active seed dataset from the latest upload
- `api/openapi.yaml`: active API contract from the latest upload
- `ops/docker-compose.yml`: active runtime topology from the latest upload
- `services/*`: runnable service code, using latest uploaded Access/FaceMatch/Migration/Notifier code plus an adapted Identity service compatible with the active schema
- `scripts/load_seed.py`: active seed loader from the latest upload

## What is preserved from V2
- `extras/ibero_identity_access_migration_package_v2.zip`
- `extras/original_v2_unpacked/`
- `dataset/*.v2.csv` for reference datasets not present in the latest upload

## Important compatibility note
The original V2 `identity-service` targeted a different schema namespace and build layout. In this merged package it was adapted to the active public-schema model so the full stack can coexist and run together.

## Services
- identity-service: `:8001`
- facematch-service: `:8002`
- access-service: `:8003`
- migration-service: `:8004`
- notifier-service: `:8005`

## Boot
```bash
cd ops
docker compose up --build
```

## Seed
```bash
docker compose exec identity-service python /app/scripts/load_seed.py
```

## Quick checks
- `GET /health` on each service
- run `flows/sample_requests.sh`
