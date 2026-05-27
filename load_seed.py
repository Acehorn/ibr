import csv
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

BASE = Path(__file__).resolve().parents[2]
DATASET = BASE / 'dataset'
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')


def read_csv(name):
    with open(DATASET / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
        for row in read_csv('campuses.csv'):
            cur.execute('''INSERT INTO campuses (legacy_system, legacy_id, code, name, city, status)
                           VALUES (%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, city=EXCLUDED.city, status=EXCLUDED.status''',
                        (row['legacy_system'], row['legacy_id'], row['code'], row['name'], row['city'], row['status']))
        for row in read_csv('programs.csv'):
            cur.execute('''INSERT INTO programs (legacy_system, legacy_id, code, name, academic_level, status)
                           VALUES (%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, academic_level=EXCLUDED.academic_level, status=EXCLUDED.status''',
                        (row['legacy_system'], row['legacy_id'], row['code'], row['name'], row['academic_level'], row['status']))
        for row in read_csv('persons.csv'):
            cur.execute('SELECT campus_id FROM campuses WHERE code=%s', (row['campus_code'],))
            campus = cur.fetchone()
            program = None
            if row['program_code']:
                cur.execute('SELECT program_id FROM programs WHERE code=%s', (row['program_code'],))
                program = cur.fetchone()
            cur.execute('''INSERT INTO persons (legacy_system, legacy_id, external_ref, institutional_id, person_type, first_name, last_name, email, phone, program_id, campus_id, status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (institutional_id) DO UPDATE SET first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name, status=EXCLUDED.status''',
                        (row['legacy_system'], row['legacy_id'], row['external_ref'], row['institutional_id'], row['person_type'], row['first_name'], row['last_name'], row['email'], row['phone'], program['program_id'] if program else None, campus['campus_id'], row['status']))
        for row in read_csv('access_points.csv'):
            cur.execute('SELECT campus_id FROM campuses WHERE code=%s', (row['campus_code'],))
            campus = cur.fetchone()
            cur.execute('''INSERT INTO access_points (campus_id, code, name, building, zone, direction_mode, status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, status=EXCLUDED.status''',
                        (campus['campus_id'], row['code'], row['name'], row['building'], row['zone'], row['direction_mode'], row['status']))
        for row in read_csv('devices.csv'):
            cur.execute('SELECT access_point_id FROM access_points WHERE code=%s', (row['access_point_code'],))
            ap = cur.fetchone()
            cur.execute('''INSERT INTO devices (access_point_id, code, device_type, serial_number, ip_address, firmware_version, status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (code) DO UPDATE SET status=EXCLUDED.status, firmware_version=EXCLUDED.firmware_version''',
                        (ap['access_point_id'], row['code'], row['device_type'], row['serial_number'], row['ip_address'], row['firmware_version'], row['status']))
        for row in read_csv('credentials.csv'):
            cur.execute('SELECT person_id FROM persons WHERE institutional_id=%s', (row['institutional_id'],))
            p = cur.fetchone()
            cur.execute('''INSERT INTO credentials (person_id, credential_code, credential_type, status, expires_at)
                           VALUES (%s,%s,%s,%s,%s)
                           ON CONFLICT (credential_code) DO UPDATE SET status=EXCLUDED.status, expires_at=EXCLUDED.expires_at''',
                        (p['person_id'], row['credential_code'], row['credential_type'], row['status'], row['expires_at']))
        for row in read_csv('biometric_profiles.csv'):
            cur.execute('SELECT person_id FROM persons WHERE institutional_id=%s', (row['institutional_id'],))
            p = cur.fetchone()
            cur.execute('''INSERT INTO biometric_profiles (person_id, provider_name, provider_profile_ref, template_hash, template_version, liveness_enabled, status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                        (p['person_id'], row['provider_name'], row['provider_profile_ref'], row['template_hash'], row['template_version'], row['liveness_enabled'].lower() == 'true', row['status']))
        for row in read_csv('access_policies.csv'):
            cur.execute('SELECT person_id FROM persons WHERE institutional_id=%s', (row['institutional_id'],))
            p = cur.fetchone()
            cur.execute('SELECT access_point_id FROM access_points WHERE code=%s', (row['access_point_code'],))
            ap = cur.fetchone()
            cur.execute('''INSERT INTO access_policies (person_id, access_point_id, weekday_mask, start_time, end_time, min_face_score, allow_entry, allow_exit, rule_reason, status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                        (p['person_id'], ap['access_point_id'], row['weekday_mask'], row['start_time'], row['end_time'], row['min_face_score'], row['allow_entry'].lower() == 'true', row['allow_exit'].lower() == 'true', row['rule_reason'], row['status']))
        conn.commit()
    print('Seed loaded successfully.')


if __name__ == '__main__':
    main()
