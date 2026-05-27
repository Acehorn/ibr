import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.common.db import get_conn
from services.common.utils import new_id

app = FastAPI(title="access-service")

class AccessDecisionRequest(BaseModel):
    person_id: str
    device_code: str
    access_point_code: str
    event_type: str
    direction: str
    validation_id: str
    credential_type: Optional[str] = 'face'

@app.get('/health')
def health():
    return {"status": "ok", "service": "access-service"}

@app.post('/access/decision')
def decide(payload: AccessDecisionRequest):
    now = datetime.utcnow()
    weekday = now.isoweekday()
    current_time = now.time()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT device_id, access_point_id FROM ibero.devices d JOIN ibero.access_points ap ON ap.access_point_id=d.access_point_id WHERE d.device_code=%s AND ap.point_code=%s", (payload.device_code, payload.access_point_code))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail='device/access point not found')
            device_id, access_point_id = row

            cur.execute("SELECT face_result, face_distance, face_threshold FROM ibero.validation_results WHERE validation_id=%s", (payload.validation_id,))
            v = cur.fetchone()
            if not v:
                raise HTTPException(status_code=404, detail='validation not found')
            face_result, face_distance, face_threshold = v

            cur.execute("""
                SELECT min_face_score, allowed_days, allowed_start_time, allowed_end_time
                FROM ibero.access_policies
                WHERE status='active' AND (person_id=%s OR person_type=(SELECT person_type FROM ibero.persons WHERE person_id=%s))
                  AND (access_point_id=%s OR access_point_id IS NULL)
                ORDER BY CASE WHEN person_id IS NOT NULL THEN 0 ELSE 1 END
                LIMIT 1
            """, (payload.person_id, payload.person_id, access_point_id))
            pol = cur.fetchone()
            policy_ok = False
            min_face_score = 0.70
            deny_reason = None
            if pol:
                min_face_score, allowed_days, start_t, end_t = pol
                day_ok = (allowed_days is None) or (weekday in allowed_days)
                time_ok = (start_t is None or current_time >= start_t) and (end_t is None or current_time <= end_t)
                policy_ok = day_ok and time_ok
            else:
                deny_reason = 'NO_POLICY'

            score = (1 - float(face_distance)) if face_distance is not None else 0.0
            if face_result == 'MATCH' and policy_ok and score >= float(min_face_score):
                decision = 'ALLOW'
            elif face_result == 'NO_MATCH':
                decision = 'DENY'
                deny_reason = deny_reason or 'NO_MATCH'
            else:
                decision = 'REVIEW' if policy_ok else 'DENY'
                deny_reason = deny_reason or ('LOW_SCORE' if policy_ok else 'OUT_OF_POLICY')

            event_id = new_id('acc')
            cur.execute("""
                INSERT INTO ibero.access_events (
                  access_event_id, person_id, device_id, access_point_id, event_type, direction,
                  credential_type, validation_id, access_result, deny_reason, occurred_at_utc
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
            """, (event_id, payload.person_id, device_id, access_point_id, payload.event_type, payload.direction,
                  payload.credential_type, payload.validation_id, decision, deny_reason))

            outbox_payload = json.dumps({
                "access_event_id": event_id,
                "person_id": payload.person_id,
                "decision": decision,
                "reason": deny_reason,
                "device_code": payload.device_code,
                "access_point_code": payload.access_point_code,
            })
            cur.execute("""
                INSERT INTO ibero.audit_log (audit_id, aggregate_type, aggregate_id, action, actor_type, payload_json)
                VALUES (%s,'access_event',%s,'decision','system',%s::jsonb)
            """, (new_id('aud'), event_id, outbox_payload))
            cur.execute("""
                INSERT INTO ibero.integration_outbox (event_id, aggregate_type, aggregate_id, event_type, payload_json)
                VALUES (%s,'access_event',%s,%s,%s::jsonb)
            """, (new_id('evt'), event_id, f'access.{decision.lower()}', outbox_payload))
    return {"access_event_id": event_id, "decision": decision, "deny_reason": deny_reason, "score": score}
