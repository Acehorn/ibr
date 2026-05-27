# Arquitectura propuesta

## Objetivo
Separar identidad, biometría y acceso físico en servicios simples de operar y fáciles de migrar.

## Componentes
- **Portal / Admin**: operación, altas, revisión y dashboards.
- **Identity Service**: personas, identidades, media y credenciales.
- **FaceMatch Service**: enrolamiento, verificación y generación de `validation_results`.
- **Access Service**: lectura de política, decisión y persistencia de `access_events`.
- **Migration Service**: adaptadores a tablas viejas y carga incremental.
- **Notifier Service**: publicación downstream desde `integration_outbox`.
- **PostgreSQL**: storage principal.
- **Object Storage**: evidencias y snapshots.

## Principios
1. Mantener IDs de legado cuando existan.
2. No romper operación actual mientras migra.
3. Guardar trazabilidad completa por evento.
4. Separar score biométrico de decisión final.
5. Facilitar reemplazo de proveedor biométrico.
