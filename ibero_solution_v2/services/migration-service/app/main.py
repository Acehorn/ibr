from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from services.common.db import get_conn
from services.common.utils import new_id

app = FastAPI(title="migration-service")

class LegacyImportRequest(BaseModel):
    source_system: str
    records: List[Dict[str, Any]]

@app.get('/health')
def health():
    return {"status": "ok", "service": "migration-service"}

@app.post('/migration/legacy/persons:import', status_code=202)
def import_persons(payload: LegacyImportRequest):
    inserted = 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            for rec in payload.records:
                person_id = rec.get('person_id') or new_id('prs')
                cur.execute("""
                    INSERT INTO ibero.persons (
                      person_id, legacy_system, legacy_id, person_type, institutional_id,
                      first_name, last_name, second_last_name, email, phone, campus_id, program_id, status
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (person_id) DO NOTHING
                """, (
                    person_id, payload.source_system, rec.get('legacy_id'), rec.get('person_type', 'student'),
                    rec.get('institutional_id'), rec.get('first_name', 'N/A'), rec.get('last_name', 'N/A'),
                    rec.get('second_last_name'), rec.get('email'), rec.get('phone'),
                    rec.get('campus_id'), rec.get('program_id'), rec.get('status', 'active')
                ))
                inserted += cur.rowcount
    return {"accepted": len(payload.records), "inserted": inserted}
