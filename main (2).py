import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')
app = FastAPI(title='Identity Service', version='1.0.0')


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class PersonCreate(BaseModel):
    legacySystem: str | None = None
    legacyId: str | None = None
    externalRef: str | None = None
    institutionalId: str | None = None
    personType: str
    firstName: str
    lastName: str
    email: EmailStr | None = None
    phone: str | None = None
    programCode: str | None = None
    campusCode: str | None = None
    status: str = 'ACTIVE'


class IdentityCreate(BaseModel):
    personId: str
    country: str | None = None
    idType: str
    idValue: str | None = None
    idValueHash: str | None = None
    isPrimary: bool = True


class CredentialCreate(BaseModel):
    personId: str
    credentialCode: str
    credentialType: str = 'QR'
    status: str = 'ACTIVE'
    expiresAt: str | None = None


@app.get('/health')
def health():
    return {'ok': True, 'service': 'identity'}


@app.post('/persons', status_code=201)
def create_person(req: PersonCreate):
    with get_conn() as conn, conn.cursor() as cur:
        campus_id = None
        program_id = None
        if req.campusCode:
            cur.execute('SELECT campus_id FROM campuses WHERE code=%s', (req.campusCode,))
            campus = cur.fetchone()
            if not campus:
                raise HTTPException(404, 'campus not found')
            campus_id = campus['campus_id']
        if req.programCode:
            cur.execute('SELECT program_id FROM programs WHERE code=%s', (req.programCode,))
            program = cur.fetchone()
            if not program:
                raise HTTPException(404, 'program not found')
            program_id = program['program_id']
        cur.execute('''INSERT INTO persons (legacy_system, legacy_id, external_ref, institutional_id, person_type, first_name, last_name, email, phone, program_id, campus_id, status)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING person_id''',
                    (req.legacySystem, req.legacyId, req.externalRef, req.institutionalId, req.personType, req.firstName, req.lastName, req.email, req.phone, program_id, campus_id, req.status))
        row = cur.fetchone()
        conn.commit()
        return {'personId': str(row['person_id'])}


@app.get('/persons/{person_id}')
def get_person(person_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('SELECT * FROM persons WHERE person_id=%s', (person_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, 'person not found')
        return row


@app.post('/identities', status_code=201)
def create_identity(req: IdentityCreate):
    # Compatible endpoint; data persisted in audit until table is formalized in next schema iteration.
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('SELECT person_id FROM persons WHERE person_id=%s', (req.personId,))
        person = cur.fetchone()
        if not person:
            raise HTTPException(404, 'person not found')
        cur.execute('''INSERT INTO audit_log (aggregate_type, aggregate_id, action, actor_type, payload_json)
                       VALUES ('identity', %s, 'identity_registered', 'api', %s)
                       RETURNING audit_id''',
                    (req.personId, {'country': req.country, 'idType': req.idType, 'idValueHash': req.idValueHash, 'isPrimary': req.isPrimary}))
        row = cur.fetchone()
        conn.commit()
        return {'identityRecordId': str(row['audit_id'])}


@app.post('/credentials', status_code=201)
def create_credential(req: CredentialCreate):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('SELECT person_id FROM persons WHERE person_id=%s', (req.personId,))
        person = cur.fetchone()
        if not person:
            raise HTTPException(404, 'person not found')
        cur.execute('''INSERT INTO credentials (person_id, credential_code, credential_type, status, expires_at)
                       VALUES (%s,%s,%s,%s,%s)
                       RETURNING credential_id''',
                    (req.personId, req.credentialCode, req.credentialType, req.status, req.expiresAt))
        row = cur.fetchone()
        conn.commit()
        return {'credentialId': str(row['credential_id'])}
