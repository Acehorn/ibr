import csv
import io
import os
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')
app = FastAPI(title='Migration Service', version='1.0.0')


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class ImportPayload(BaseModel):
    sourceSystem: str
    records: list[dict]


@app.get('/health')
def health():
    return {'ok': True, 'service': 'migration'}


@app.post('/migration/legacy/persons:import', status_code=202)
def import_persons(payload: ImportPayload):
    imported = 0
    errors = []
    with get_conn() as conn, conn.cursor() as cur:
        for row in payload.records:
            try:
                cur.execute('SELECT campus_id FROM campuses WHERE code=%s', (row['campus_code'],))
                campus = cur.fetchone()
                cur.execute('SELECT program_id FROM programs WHERE code=%s', (row.get('program_code'),)) if row.get('program_code') else None
                program = cur.fetchone() if row.get('program_code') else None
                cur.execute('''INSERT INTO persons (legacy_system, legacy_id, external_ref, institutional_id, person_type, first_name, last_name, email, phone, program_id, campus_id, status)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                               ON CONFLICT (institutional_id) DO UPDATE SET
                                 first_name=EXCLUDED.first_name,
                                 last_name=EXCLUDED.last_name,
                                 email=EXCLUDED.email,
                                 phone=EXCLUDED.phone,
                                 status=EXCLUDED.status,
                                 updated_at=now()''',
                            (payload.sourceSystem, row.get('legacy_id'), row.get('external_ref'), row.get('institutional_id'), row['person_type'], row['first_name'], row['last_name'], row.get('email'), row.get('phone'), program['program_id'] if program else None, campus['campus_id'] if campus else None, row.get('status', 'ACTIVE')))
                imported += 1
            except Exception as exc:
                errors.append({'row': row, 'error': str(exc)})
        conn.commit()
    return {'accepted': imported, 'errors': errors[:20]}


@app.post('/migration/legacy/persons:import-csv', status_code=202)
def import_persons_csv(payload: dict):
    text = payload['csvText']
    source = payload.get('sourceSystem', 'legacy_csv')
    records = list(csv.DictReader(io.StringIO(text)))
    return import_persons(ImportPayload(sourceSystem=source, records=records))
