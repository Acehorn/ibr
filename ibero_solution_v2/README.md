# IBERO Identity + FaceMatch + Access Control Migration Package v2

Paquete técnico completo para migrar lo que IBERO ya tenga a un flujo nuevo, neutral y funcional.

## Qué incluye
- `db/000_schema.sql`: esquema PostgreSQL completo orientado a identidad, biometría, accesos y auditoría.
- `dataset/*.csv`: dataset semilla de campus, personas, identidades, credenciales, dispositivos, políticas y eventos.
- `api/openapi.yaml`: contratos OpenAPI 3.0 del dominio.
- `services/*`: microservicios FastAPI listos para arrancar localmente.
- `flows/ibero_flow.md`: flujo operativo end-to-end y decisiones.
- `docs/migration_mapping.md`: mapeo de legado -> nuevo dominio.
- `ops/docker-compose.yml`: stack local para pruebas.
- `scripts/load_seed.py`: cargador rápido del dataset a PostgreSQL.

## Dominio cubierto
- Alumnos, staff, visitantes y contratistas
- Identidad documental e institucional
- Enrolamiento biométrico
- Verificación facial con puntaje y threshold
- Decisión de acceso por política y horario
- Trazabilidad, auditoría y outbox
- Migración incremental desde sistema legado

## Nodos / servicios
1. `identity-service`: altas, identidades, media y credenciales.
2. `facematch-service`: enrolamiento y verificación facial.
3. `access-service`: decisión de acceso y registro de eventos.
4. `migration-service`: ingesta desde legado y transformación.
5. `notifier-service`: consumo de outbox / health placeholder.
6. `postgres`: almacenamiento principal.

## Arranque rápido
```bash
cd ops
docker compose up --build
```

## Carga rápida del dataset
```bash
python scripts/load_seed.py
```

## Puertos por defecto
- identity-service: `8001`
- facematch-service: `8002`
- access-service: `8003`
- migration-service: `8004`
- notifier-service: `8005`
- postgres: `5432`

## Decisión operativa resumida
1. Crear persona.
2. Registrar identidad y credencial.
3. Enrolar biométrico.
4. Dispositivo solicita verificación facial.
5. Access service valida política + score.
6. Se guarda `access_events`, `audit_log` y `integration_outbox`.
