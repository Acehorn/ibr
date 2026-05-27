import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.common.db import get_conn
from services.common.utils import new_id, sha256_text

app = FastAPI(title="identity-service")

class PersonCreate(BaseModel):
    person_id: Optional[str] = None
    legacy_system: Optional[str] = None
    legacy_id: Optional[str] = None
    person_type: str
    institutional_id: Optional[str] = None
    first_name: str
    last_name: str
    second_last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    campus_id: Optional[str] = None
    program_id: Optional[str] = None
    status: str = "active"

class IdentityCreate(BaseModel):
    identity_id: Optional[str] = None
    person_id: str
    country: Optional[str] = None
    id_type: str
    id_value: Optional[str] = None
    id_value_hash: Optional[str] = None
    is_primary: bool = True

class CredentialCreate(BaseModel):
    credential_id: Optional[str] = None
    person_id: str
    credential_type: str
    credential_value: Optional[str] = None
    credential_value_hash: Optional[str] = None
    valid_from_utc: Optional[str] = None
    valid_until_utc: Optional[str] = None

@app.get('/health')
def health():
    return {"status": "ok", "service": "identity-service"}

@app.post('/persons', status_code=201)
def create_person(payload: PersonCreate):
    person_id = payload.person_id or new_id('prs')
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ibero.persons (
                  person_id, legacy_system, legacy_id, person_type, institutional_id,
                  first_name, last_name, second_last_name, email, phone, campus_id, program_id, status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING person_id
            """, (
                person_id, payload.legacy_system, payload.legacy_id, payload.person_type,
                payload.institutional_id, payload.first_name, payload.last_name,
                payload.second_last_name, payload.email, payload.phone,
                payload.campus_id, payload.program_id, payload.status
            ))
            cur.execute("""
                INSERT INTO ibero.audit_log (audit_id, aggregate_type, aggregate_id, action, actor_type, payload_json)
                VALUES (%s,'person',%s,'created','system',%s::jsonb)
            """, (new_id('aud'), person_id, payload.model_dump_json()))
    return {"person_id": person_id}

@app.get('/persons/{person_id}')
def get_person(person_id: str):
    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM ibero.persons WHERE person_id=%s", (person_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail='person not found')
            return row

@app.post('/identities', status_code=201)
def create_identity(payload: IdentityCreate):
    identity_id = payload.identity_id or new_id('idn')
    id_hash = payload.id_value_hash or (sha256_text(payload.id_value) if payload.id_value else None)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ibero.identities (identity_id, person_id, country, id_type, id_value, id_value_hash, is_primary)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (identity_id, payload.person_id, payload.country, payload.id_type, payload.id_value, id_hash, payload.is_primary))
    return {"identity_id": identity_id}

@app.post('/credentials', status_code=201)
def create_credential(payload: CredentialCreate):
    credential_id = payload.credential_id or new_id('crd')
    value_hash = payload.credential_value_hash or (sha256_text(payload.credential_value) if payload.credential_value else None)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ibero.credentials (
                  credential_id, person_id, credential_type, credential_value, credential_value_hash,
                  valid_from_utc, valid_until_utc
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (credential_id, payload.person_id, payload.credential_type, payload.credential_value, value_hash, payload.valid_from_utc, payload.valid_until_utc))
    return {"credential_id": credential_id}
