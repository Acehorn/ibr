from fastapi import FastAPI
from services.common.db import get_conn

app = FastAPI(title="notifier-service")

@app.get('/health')
def health():
    return {"status": "ok", "service": "notifier-service"}

@app.get('/outbox/pending')
def pending(limit: int = 50):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT event_id, aggregate_type, aggregate_id, event_type, payload_json, occurred_at_utc FROM ibero.integration_outbox WHERE status='PENDING' ORDER BY occurred_at_utc LIMIT %s", (limit,))
            rows = cur.fetchall()
    return {"items": rows}
