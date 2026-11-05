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
        migrate(c)
        c.execute(
            "TRUNCATE endpoint_checkpoints, source_items, current_offers, import_runs, staging, domain_checkpoints, source_state, index_outbox, source_schema, observations, relationships RESTART IDENTITY CASCADE"
        )
        yield c
