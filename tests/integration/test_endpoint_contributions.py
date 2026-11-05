from datetime import timedelta

import pytest

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogError,
    Observation,
    SourceItem,
    utcnow,
)
from suppliermcp.catalog.repository import get_product
from suppliermcp.sync.publish import publish, stage


def put(conn, endpoint, rows, **kw):
    return publish(
        conn,
        stage(
            conn, BatchManifest(interface="mega", domain="schema", endpoint=endpoint, **kw), rows
        ),
    )


def product(endpoint, values, id="1"):
    return SourceItem(
        supplier="mega",
        source_id=id,
        sku="00" + id,
        name="Product",
        observations=[
            Observation(
                interface="mega",
                endpoint=endpoint,
                field="color",
                value=v,
                value_key=v,
                cardinality="many",
            )
            for v in values
        ],
    )


def test_independent_endpoint_checkpoints(conn):
    t = utcnow()
    put(
        conn,
        "B",
        [SourceItem(supplier="mega", source_id="1", sku="001", name="First")],
        started_at=t,
    )
    put(
        conn,
        "A",
        [SourceItem(supplier="mega", source_id="2", sku="002", name="Second")],
        started_at=t - timedelta(minutes=1),
    )
    assert get_product(conn, "mega:2").item.name == "Second"


def test_empty_replacement_removes_only_own_endpoint(conn):
    put(conn, "A", [product("A", ["red", "blue"])], replace_scope="endpoint")
    put(conn, "B", [product("B", ["green"])], replace_scope="endpoint")
    assert {o.value for o in get_product(conn, "mega:1").item.observations} == {
        "red",
        "blue",
        "green",
    }
    put(conn, "A", [], replace_scope="endpoint")
    assert {o.value for o in get_product(conn, "mega:1").item.observations} == {"green"}
    assert get_product(conn, "mega:1").item.name == "Product"


def test_targeted_replacement_preserves_other_items(conn):
    put(
        conn, "A", [product("A", ["red"]), product("A", ["blue"], id="2")], replace_scope="endpoint"
    )
    put(conn, "A", [product("A", ["green"])], replace_scope="items", mode="targeted")
    assert {o.value for o in get_product(conn, "mega:1").item.observations} == {"green"}
    assert {o.value for o in get_product(conn, "mega:2").item.observations} == {"blue"}


def test_failed_final_record_cannot_replace_endpoint(conn):
    put(conn, "A", [product("A", ["red"])], replace_scope="endpoint")

    def broken():
        yield product("A", ["blue"])
        raise CatalogError("invalid_export")

    with pytest.raises(CatalogError, match="invalid_export"):
        put(conn, "A", broken(), replace_scope="endpoint")
    assert {o.value for o in get_product(conn, "mega:1").item.observations} == {"red"}


def test_enrichment_cannot_retire_identity(conn):
    m = BatchManifest(
        interface="mega",
        domain="catalog",
        endpoint="base",
        complete=True,
        authoritative_identity=True,
    )
    publish(conn, stage(conn, m, [product("base", [], str(i)) for i in range(4)]))
    m = BatchManifest(
        interface="mega",
        domain="catalog",
        endpoint="extra",
        complete=True,
        authoritative_identity=False,
    )
    publish(conn, stage(conn, m, [product("extra", [])]))
    assert conn.execute("SELECT count(*) FROM source_items WHERE active").fetchone()[0] == 4


def test_migration_preserves_legacy_evidence(conn):
    from pathlib import Path

    from suppliermcp.catalog.db import migrate

    with conn.transaction():
        conn.execute("CREATE SCHEMA legacy_upgrade")
        conn.execute("SET LOCAL search_path TO legacy_upgrade")
        conn.execute("CREATE TABLE migrations(name text PRIMARY KEY)")
        for path in sorted(Path("migrations").glob("00[1-4]*.sql")):
            conn.execute(path.read_text())
            conn.execute("INSERT INTO migrations VALUES (%s)", (path.name,))
        conn.execute(
            "INSERT INTO observations VALUES ('mega:7','mega','base','Name','{\"value\":\"Original\"}')"
        )
        migrate(conn)
        assert conn.execute("SELECT data,value_key FROM observations").fetchone() == (
            {"value": "Original"},
            "",
        )
        conn.execute("SET LOCAL search_path TO public")
        conn.execute("DROP SCHEMA legacy_upgrade CASCADE")


def test_parameter_rows_publish_without_replacing_identity(conn):
    from suppliermcp.catalog.contracts import SchemaRecord

    put(conn, "base", [product("base", [])])
    fact = Observation(
        interface="mega",
        endpoint="params",
        field="parameter:42",
        value="red",
        value_key="a",
        cardinality="many",
    )
    put(
        conn,
        "params",
        [
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={"item_id": "mega:1", "observations": [fact.model_dump(mode="json")]},
            )
        ],
        replace_scope="endpoint",
    )
    view = get_product(conn, "mega:1")
    assert view.item.name == "Product"
    assert [(o.field, o.value) for o in view.item.observations] == [("parameter:42", "red")]
