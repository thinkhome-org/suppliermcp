from pathlib import Path

import psycopg

from suppliermcp.catalog.contracts import CatalogError


def connect(settings):
    try:
        return psycopg.connect(
            settings.database_url.get_secret_value(), autocommit=True, connect_timeout=5
        )
    except psycopg.Error:
        raise CatalogError("service_unavailable", retryable=True) from None


def migrate(conn):
    root = Path(__file__).resolve().parents[3] / "migrations"
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(91001)")
        conn.execute("CREATE TABLE IF NOT EXISTS migrations (name text PRIMARY KEY)")
        for path in sorted(root.glob("*.sql")):
            if not conn.execute("SELECT 1 FROM migrations WHERE name=%s", (path.name,)).fetchone():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO migrations VALUES (%s)", (path.name,))
