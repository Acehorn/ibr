# Flujo operativo IBERO

## A. Alta / migración
1. `migration-service` recibe registros viejos.
2. Normaliza a `persons`, `identities`, `credentials` y `biometric_profiles`.
3. Inserta bitácora en `audit_log`.

## B. Enrolamiento biométrico
1. Portal o nodo edge llama `POST /biometrics/enroll`.
2. Se genera `biometric_profile_id`.
3. Se registra `validation_results` con `validation_type=face_enrollment`.

## C. Verificación facial
1. Dispositivo envía candidato a `POST /facematch/verify`.
2. Servicio calcula score simulado/real del proveedor.
3. Se genera `validation_results` con `MATCH/NO_MATCH/NO_FACE`.

## D. Decisión de acceso
1. Nodo invoca `POST /access/decision` con persona, punto y `validation_id`.
2. `access-service` revisa política, score y horario.
3. Devuelve `ALLOW`, `DENY` o `REVIEW`.
4. Persiste `access_events`, `audit_log` y `integration_outbox`.

## E. Notificación / downstream
1. `notifier-service` consulta outbox pendiente.
2. Reenvía a integraciones, dashboard, correo o webhook.

## Reglas mínimas sugeridas
- `MATCH` + score >= threshold + política vigente = `ALLOW`
- `NO_MATCH` = `DENY`
- Sin política o score dudoso = `REVIEW`
