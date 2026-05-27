import csv
import os
from pathlib import Path
import psycopg

BASE = Path(__file__).resolve().parents[1]
DATASET = BASE / 'dataset'

conn = psycopg.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    dbname=os.getenv('DB_NAME', 'ibero'),
    user=os.getenv('DB_USER', 'ibero'),
    password=os.getenv('DB_PASSWORD', 'ibero'),
)

TABLES = [
    ('campuses.csv', 'ibero.campuses', ['campus_id','campus_code','campus_name','city','status']),
    ('programs.csv', 'ibero.programs', ['program_id','program_code','program_name','academic_level','campus_id','status']),
    ('persons.csv', 'ibero.persons', ['person_id','legacy_system','legacy_id','person_type','institutional_id','first_name','last_name','second_last_name','email','phone','campus_id','program_id','status']),
    ('identities.csv', 'ibero.identities', ['identity_id','person_id','country','id_type','id_value','id_value_hash','is_primary']),
    ('biometric_profiles.csv', 'ibero.biometric_profiles', ['biometric_profile_id','person_id','provider_name','provider_profile_ref','template_hash','template_version','liveness_enabled','status']),
    ('credentials.csv', 'ibero.credentials', ['credential_id','person_id','credential_type','credential_value','credential_value_hash','status','valid_from_utc','valid_until_utc']),
    ('access_points.csv', 'ibero.access_points', ['access_point_id','campus_id','point_code','point_name','point_type','is_active']),
    ('devices.csv', 'ibero.devices', ['device_id','access_point_id','device_code','device_type','vendor','serial_number','status']),
    ('access_policies.csv', 'ibero.access_policies', ['policy_id','person_id','person_type','campus_id','access_point_id','allowed_start_time','allowed_end_time','allowed_days','min_face_score','status']),
]

with conn:
    with conn.cursor() as cur:
        for filename, table, columns in TABLES:
            path = DATASET / filename
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    values = [row.get(c) or None for c in columns]
                    if 'allowed_days' in columns:
                        idx = columns.index('allowed_days')
                        values[idx] = [int(x) for x in row['allowed_days'].split('|')] if row.get('allowed_days') else None
                    placeholders = ','.join(['%s'] * len(columns))
                    cur.execute(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                        values,
                    )
print('seed loaded')
