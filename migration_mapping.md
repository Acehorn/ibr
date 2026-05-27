# Mapeo sugerido de migración desde legado

## Entidades mínimas a rescatar
- alumnos
- personal
- visitantes frecuentes
- matrículas / ids institucionales
- programas / carreras
- campus / edificios / accesos
- credenciales vigentes / expiradas
- fotos de referencia o embeddings existentes
- bitácora histórica de entradas y salidas
- bajas, bloqueos, restricciones y listas negras

## Mapeo recomendado
| Legado | Nuevo modelo |
|---|---|
| student_id | persons.external_ref |
| enrollment | persons.institutional_id |
| full_name | persons.first_name + last_name |
| role/student/staff | persons.person_type |
| campus_name | campuses.name |
| access_point | access_points.name |
| badge_status | credentials.status |
| face_template_id | biometric_profiles.provider_profile_ref |
| access_log | access_events |
| check_in/check_out | access_events.direction |
| photo_url | biometric_artifacts.artifact_uri |
| block_reason | access_policies.rule_reason |

## Estrategia de migración
1. Catálogos
2. Personas
3. Credenciales
4. Biométricos
5. Políticas de acceso
6. Bitácora histórica
7. Validación cruzada
8. Cutover por plantel o edificio

## Reglas prácticas
- Mantener `legacy_system` y `legacy_id` en todas las tablas críticas.
- Nunca sobreescribir histórico; versionar estado.
- Separar artefacto biométrico de metadata operacional.
- Guardar score, umbral y evidencia por decisión.
