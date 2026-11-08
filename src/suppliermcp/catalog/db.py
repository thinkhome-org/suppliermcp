import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.data import data_dir
from suppliermcp.sync.lifecycle import check_abort, register_connection


def connection_info(settings):
    dsn = settings.database_url.get_secret_value()
    options = conninfo_to_dict(dsn).get("options", "")
    # Bound lost sockets on both ends; healthy long statements/COPY remain unrestricted.
    options += " -c tcp_keepalives_idle=30 -c tcp_keepalives_interval=10 -c tcp_keepalives_count=3 -c tcp_user_timeout=60000"
    return make_conninfo(
        dsn,
        options=options.strip(),
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
        tcp_user_timeout=60000,
    )


def connect(settings):
    try:
        check_abort()
        return register_connection(
            psycopg.connect(connection_info(settings), autocommit=True, connect_timeout=5)
        )
    except psycopg.Error:
        raise CatalogError("service_unavailable", retryable=True) from None


def migrate(conn):
    paths = sorted(data_dir("migrations").glob("*.sql"))
    if not paths:
        raise RuntimeError("Missing migration SQL")
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(91001)")
        conn.execute("CREATE TABLE IF NOT EXISTS migrations (name text PRIMARY KEY)")
        for path in paths:
            if not conn.execute("SELECT 1 FROM migrations WHERE name=%s", (path.name,)).fetchone():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO migrations VALUES (%s)", (path.name,))


def require_projected_catalog(conn):
    if not conn.execute("SELECT 1 FROM migrations WHERE name='011_clean_catalog.sql'").fetchone():
        raise CatalogError(
            "catalog_migration_required",
            "Initialize a clean v2 database and reimport through the v2 adapters. See docs/operations.md.",
        )
