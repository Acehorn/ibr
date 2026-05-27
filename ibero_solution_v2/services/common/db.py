import os
from contextlib import contextmanager
import psycopg

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "ibero"),
    "user": os.getenv("DB_USER", "ibero"),
    "password": os.getenv("DB_PASSWORD", "ibero"),
}

@contextmanager
def get_conn():
    conn = psycopg.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
