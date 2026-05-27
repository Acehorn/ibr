import os
import hashlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')
app = FastAPI(title='FaceMatch Service', version='1.0.0')


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class EnrollRequest(BaseModel):
    personId: str
    providerName: str = 'internal'
    providerProfileRef: str | None = None
    templateHash: str
    templateVersion: str | None = 'v1'
    livenessEnabled: bool = True


class VerifyRequest(BaseModel):
    personHint: str | None = None
    credentialCode: str | None = None
    deviceCode: str
    accessPointCode: str
    templateHashCandidate: str
    evidenceUri: str | None = None
    providerName: str = 'internal'


@app.get('/health')
def health():
    return {'ok': True, 'service': 'facematch'}


@app.post('/biometrics/enroll', status_code=201)
def enroll(req: EnrollRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('''INSERT INTO biometric_profiles (person_id, provider_name, provider_profile_ref, template_hash, template_version, liveness_enabled)
                       VALUES (%s,%s,%s,%s,%s,%s) RETURNING biometric_profile_id''',
                    (req.personId, req.providerName, req.providerProfileRef, req.templateHash, req.templateVersion, req.livenessEnabled))
        row = cur.fetchone()
        conn.commit()
        return {'biometricProfileId': str(row['biometric_profile_id'])}


def compare_hashes(a: str, b: str) -> float:
    if a == b:
        return 0.99
    # similarity simple demo based on shared prefix digest, reemplazable por engine real
    da = hashlib.sha256(a.encode()).hexdigest()
    db = hashlib.sha256(b.encode()).hexdigest()
    same = sum(1 for x, y in zip(da, db) if x == y)
    return round(same / len(da), 4)


@app.post('/facematch/verify')
def verify(req: VerifyRequest):
    with get_conn() as conn, conn.cursor() as cur:
        person = None
        if req.personHint:
            cur.execute('SELECT person_id FROM persons WHERE institutional_id=%s OR external_ref=%s', (req.personHint, req.personHint))
            person = cur.fetchone()
        elif req.credentialCode:
            cur.execute('SELECT person_id FROM credentials WHERE credential_code=%s', (req.credentialCode,))
            person = cur.fetchone()
        if not person:
            raise HTTPException(404, 'person could not be resolved')

        cur.execute('SELECT biometric_profile_id, template_hash FROM biometric_profiles WHERE person_id=%s AND status=%s ORDER BY enrolled_at DESC LIMIT 1', (person['person_id'], 'ACTIVE'))
        profile = cur.fetchone()
        if not profile:
            raise HTTPException(404, 'active biometric profile not found')

        cur.execute('SELECT device_id FROM devices WHERE code=%s', (req.deviceCode,))
        device = cur.fetchone()
        cur.execute('SELECT access_point_id FROM access_points WHERE code=%s', (req.accessPointCode,))
        ap = cur.fetchone()
        if not device or not ap:
            raise HTTPException(404, 'device or access point not found')

        score = compare_hashes(profile['template_hash'], req.templateHashCandidate)
        threshold = 0.82
        result = 'MATCH' if score >= threshold else 'NO_MATCH'
        cur.execute('''INSERT INTO facematch_events (person_id, device_id, access_point_id, provider_name, score, threshold, result, evidence_uri, raw_json)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING facematch_event_id''',
                    (person['person_id'], device['device_id'], ap['access_point_id'], req.providerName, score, threshold, result, req.evidenceUri, {'mode': 'demo'}))
        evt = cur.fetchone()
        conn.commit()
        return {'facematchEventId': str(evt['facematch_event_id']), 'personId': str(person['person_id']), 'score': score, 'threshold': threshold, 'result': result}
