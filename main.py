import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')
app = FastAPI(title='Access Service', version='1.0.0')


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class AccessDecisionRequest(BaseModel):
    direction: str
    accessPointCode: str
    deviceCode: str
    credentialCode: str | None = None
    personId: str | None = None
    facematchEventId: str | None = None


@app.get('/health')
def health():
    return {'ok': True, 'service': 'access'}


@app.post('/access/decision')
def decide(req: AccessDecisionRequest):
    with get_conn() as conn, conn.cursor() as cur:
        person_id = req.personId
        credential_id = None
        if req.credentialCode:
            cur.execute('SELECT credential_id, person_id, status FROM credentials WHERE credential_code=%s', (req.credentialCode,))
            cred = cur.fetchone()
            if not cred:
                raise HTTPException(404, 'credential not found')
            credential_id = cred['credential_id']
            person_id = cred['person_id']
            if cred['status'] != 'ACTIVE':
                raise HTTPException(403, 'credential inactive')
        if req.facematchEventId:
            cur.execute('SELECT score, threshold, person_id, result FROM facematch_events WHERE facematch_event_id=%s', (req.facematchEventId,))
            fm = cur.fetchone()
            if not fm:
                raise HTTPException(404, 'facematch event not found')
            if not person_id:
                person_id = fm['person_id']
        else:
            fm = None
        if not person_id:
            raise HTTPException(400, 'person unresolved')

        cur.execute('SELECT access_point_id FROM access_points WHERE code=%s', (req.accessPointCode,))
        ap = cur.fetchone()
        cur.execute('SELECT device_id FROM devices WHERE code=%s', (req.deviceCode,))
        device = cur.fetchone()
        if not ap or not device:
            raise HTTPException(404, 'device or access point not found')

        cur.execute('''SELECT * FROM access_policies
                       WHERE person_id=%s AND access_point_id=%s AND status='ACTIVE'
                       ORDER BY created_at DESC LIMIT 1''', (person_id, ap['access_point_id']))
        policy = cur.fetchone()
        if not policy:
            decision, reason = 'DENY', 'No active access policy'
        elif fm and fm['result'] != 'MATCH':
            decision, reason = 'DENY', 'Face match failed'
        else:
            now = datetime.now().time()
            if policy['start_time'] and policy['end_time'] and not (policy['start_time'] <= now <= policy['end_time']):
                decision, reason = 'DENY', 'Outside allowed time window'
            else:
                decision, reason = 'ALLOW', 'Policy and biometrics valid'

        cur.execute('''INSERT INTO access_events (person_id, credential_id, facematch_event_id, access_point_id, device_id, direction, decision, decision_reason)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING access_event_id, event_time''',
                    (person_id, credential_id, req.facematchEventId, ap['access_point_id'], device['device_id'], req.direction, decision, reason))
        event = cur.fetchone()
        cur.execute('''INSERT INTO integration_outbox (aggregate_type, aggregate_id, event_type, payload_json)
                       VALUES ('access_event', %s, 'ACCESS_DECIDED', %s)''',
                    (str(event['access_event_id']), {'decision': decision, 'reason': reason, 'person_id': str(person_id)}))
        conn.commit()
        return {'accessEventId': str(event['access_event_id']), 'decision': decision, 'reason': reason, 'eventTime': event['event_time'].isoformat()}
