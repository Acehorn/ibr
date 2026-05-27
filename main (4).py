import os
from fastapi import FastAPI
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/ibero')
app = FastAPI(title='Notifier Service', version='1.0.0')


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get('/health')
def health():
    return {'ok': True, 'service': 'notifier'}


@app.post('/outbox/dispatch')
def dispatch(limit: int = 50):
    sent = []
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('''SELECT event_id, aggregate_type, aggregate_id, event_type, payload_json
                       FROM integration_outbox WHERE status='PENDING'
                       ORDER BY occurred_at LIMIT %s''', (limit,))
        rows = cur.fetchall()
        for row in rows:
            sent.append({'eventId': str(row['event_id']), 'type': row['event_type'], 'aggregateId': row['aggregate_id']})
            cur.execute('UPDATE integration_outbox SET status=%s, delivered_at=now(), delivery_attempts=delivery_attempts+1 WHERE event_id=%s', ('DELIVERED', row['event_id']))
        conn.commit()
    return {'delivered': len(sent), 'events': sent}
