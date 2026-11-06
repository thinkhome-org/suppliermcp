import os

import psycopg
import pytest

from suppliermcp.catalog.db import migrate


@pytest.fixture
def conn():
    with psycopg.connect(
        os.getenv("SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"),
        autocommit=True,
    ) as c:
        # Concurrent pytest sessions sharing this database must not truncate each other's staged imports.
        c.execute("SELECT pg_advisory_lock(91009)")
        migrate(c)
        c.execute(
            "TRUNCATE query_results, endpoint_checkpoints, source_items, current_offers, import_runs, staging, domain_checkpoints, source_state, index_outbox, source_schema, observations, relationships RESTART IDENTITY CASCADE"
        )
        yield c
