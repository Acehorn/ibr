from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from services.common.db import get_conn
from services.common.utils import new_id

app = FastAPI(title="facematch-service")

class BiometricEnrollRequest(BaseModel):
    person_id: str
    provider_name: str = "internal"
    provider_profile_ref: Optional[str] = None
    template_hash: str
    template_version: Optional[str] = None
    liveness_enabled: bool = True

class FaceVerifyRequest(BaseModel):
    person_id: str
    device_code: str
    access_point_code: str
    candidate_template_hash: str
    evidence_uri: Optional[str] = None
    provider_name: str = "internal"

@app.get('/health')
def health():
    return {"status": "ok", "service": "facematch-service"}

@app.post('/biometrics/enroll', status_code=201)
def enroll(payload: BiometricEnrollRequest):
    profile_id = new_id('bio')
    validation_id = new_id('val')
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ibero.biometric_profiles (
                  biometric_profile_id, person_id, provider_name, provider_profile_ref,
                  template_hash, template_version, liveness_enabled
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (profile_id, payload.person_id, payload.provider_name, payload.provider_profile_ref,
                  payload.template_hash, payload.template_version, payload.liveness_enabled))
            cur.execute("""
                INSERT INTO ibero.validation_results (
                  validation_id, person_id, validator_provider, validation_type,
                  face_result, decided_status
                ) VALUES (%s,%s,%s,'face_enrollment','MATCH','OK')
            """, (validation_id, payload.person_id, payload.provider_name))
    return {"biometric_profile_id": profile_id, "validation_id": validation_id}

@app.post('/facematch/verify')
def verify(payload: FaceVerifyRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT template_hash FROM ibero.biometric_profiles WHERE person_id=%s AND status='active' ORDER BY enrolled_at_utc DESC LIMIT 1",
                (payload.person_id,)
            )
            row = cur.fetchone()
            stored = row[0] if row else None

            if not stored:
                result, distance, threshold, decision = 'NO_FACE', None, 0.5000, 'REVIEW'
            elif stored == payload.candidate_template_hash:
                result, distance, threshold, decision = 'MATCH', 0.1200, 0.5000, 'OK'
            else:
                result, distance, threshold, decision = 'NO_MATCH', 0.8400, 0.5000, 'REJECT'

            validation_id = new_id('val')
            cur.execute("""
                INSERT INTO ibero.validation_results (
                  validation_id, person_id, validator_provider, validation_type,
                  face_distance, face_threshold, face_result, decided_status, created_at_utc
                ) VALUES (%s,%s,%s,'face_verification',%s,%s,%s,%s,now())
            """, (validation_id, payload.person_id, payload.provider_name, distance, threshold, result, decision))
    return {
        "validation_id": validation_id,
        "person_id": payload.person_id,
        "face_distance": distance,
        "face_threshold": threshold,
        "face_result": result,
        "decided_status": decision
    }
