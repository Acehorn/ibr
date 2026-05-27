# Flujo operativo IBERO

## 1. Alta / migración
- Se crea persona (`student`, `staff`, `visitor`).
- Se asocia campus, programa y estatus.
- Se emite credencial.
- Se crea política de acceso.

## 2. Enrolamiento biométrico
- Cámara o app captura rostro.
- Servicio biométrico genera `template_hash` y `provider_profile_ref`.
- Se guarda perfil biométrico activo.
- Evidencia opcional se manda a object storage.

## 3. Intento de acceso
- Dispositivo manda `person_hint` o `credential_code` + imagen/live frame.
- FaceMatch calcula score y threshold aplicado.
- Access Service revisa:
  - credencial activa
  - política vigente
  - horario
  - lista de bloqueo
  - score biométrico mínimo
- Resultado: `ALLOW`, `REVIEW`, `DENY`.

## 4. Registro
- Se inserta `facematch_events`.
- Se inserta `access_events`.
- Se inserta `audit_log`.
- Se publica evento en outbox.

## 5. Consumo downstream
- Dashboard operativo
- Monitoreo de seguridad
- Notificaciones
- Reportes de asistencia y trazabilidad

## 6. Migración desde legado
- ETL toma export CSV/JSON/API del sistema actual.
- Normaliza a staging.
- Ejecuta upsert al nuevo esquema.
- Genera reporte de errores y no coincidencias.
