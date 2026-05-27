# Mapeo de migración legado -> nuevo dominio

## Ejemplo de equivalencias
| Legado | Nuevo | Notas |
|---|---|---|
| `students`, `employees`, `visitors` | `ibero.persons` | Consolidar con `person_type` |
| `official_docs`, `kyc_docs` | `ibero.identities` | Mantener `legacy_system` y `legacy_id` |
| `doc_images`, `selfies` | `ibero.media_assets` | Guardar URI y checksum |
| `face_templates`, `enrollments` | `ibero.biometric_profiles` | Reusar `provider_profile_ref` |
| `badges`, `cards`, `qr_tokens` | `ibero.credentials` | Hash del valor cuando aplique |
| `gates`, `doors`, `turnstiles` | `ibero.access_points` | Normalizar nombres y campus |
| `devices`, `readers`, `cams` | `ibero.devices` | Vincular a `access_points` |
| `access_logs`, `turnstile_logs` | `ibero.access_events` | Mapear entrada/salida/intento |
| `kyc_results`, `facematch_logs` | `ibero.validation_results` | Separar validación de decisión |

## Estrategia sugerida
1. Migrar catálogos: campus, programas, puertas, dispositivos.
2. Migrar personas e identidades.
3. Migrar credenciales activas.
4. Migrar biométricos y artefactos referenciales.
5. Reproducir histórico de accesos.
6. Ejecutar convivencia temporal con dual-write opcional.
