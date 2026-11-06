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
        import psycopg

        with pytest.raises(psycopg.errors.RaiseException, match="catalog_reprojection_required"):
            migrate(conn)
        assert conn.execute("SELECT data FROM observations").fetchone() == ({"value": "Original"},)
        assert not conn.execute("SELECT 1 FROM migrations WHERE name LIKE '011%'").fetchone()
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


def test_shop_facts_join_only_existing_supplier_sku(conn):
    from suppliermcp.catalog.contracts import SchemaRecord

    put(conn, "base", [product("base", [])])
    record = SchemaRecord(
        interface="mega",
        kind="product_facts",
        values={
            "supplier": "mega",
            "sku": "001",
            "observations": [
                Observation(
                    interface="mega", endpoint="shop", field="NAME", value="Description"
                ).model_dump(mode="json")
            ],
        },
    )
    put(conn, "shop", [record], replace_scope="items")
    assert get_product(conn, "mega:1").item.observations[0].value == "Description"
    record.values["sku"] = "unknown"
    with pytest.raises(CatalogError, match="unresolved_product_reference"):
        put(conn, "shop", [record])


def test_class_export_keeps_unmatched_sku_until_catalog_catches_up(conn):
    from suppliermcp.catalog.contracts import SchemaRecord

    endpoint = "X-StoItemClass"
    put(conn, "base", [product("base", [])])
    rows = [
        SchemaRecord(
            interface="mega",
            kind="product_facts",
            values={
                "supplier": "mega",
                "sku": sku,
                "observations": [
                    Observation(
                        interface="mega", endpoint=endpoint, field="class", value="A"
                    ).model_dump(mode="json")
                ],
            },
        )
        for sku in ("001", "002")
    ]
    options = dict(replace_scope="endpoint", artifact_sha256="a" * 64)
    put(conn, endpoint, rows, **options)
    assert get_product(conn, "mega:1").item.observations[0].value == "A"
    query = "SELECT data->>'sku' FROM source_schema WHERE kind='unmatched_product_class'"
    assert conn.execute(query).fetchall() == [("002",)]
    put(conn, "base", [product("base", [], id="2")])
    put(conn, endpoint, rows, **options)
    assert get_product(conn, "mega:2").item.observations[0].value == "A"
    assert conn.execute(query).fetchall() == []


def test_identical_empty_targeted_responses_replace_each_requested_sku(conn):
    put(conn, "A", [product("A", ["red"]), product("A", ["blue"], id="2")])
    for sku in ["001", "002"]:
        put(
            conn,
            "A",
            [],
            requested_skus=[sku],
            replace_scope="items",
            mode="targeted",
            artifact_sha256="same-empty-body",
        )
    assert not get_product(conn, "mega:2").item.observations


def test_replaying_unchanged_run_keeps_original_revision(conn):
    first = put(conn, "A", [product("A", ["red"])], artifact_sha256="first")
    run_id = stage(
        conn,
        BatchManifest(interface="mega", domain="schema", endpoint="A", artifact_sha256="first"),
        [product("A", ["red"])],
    )
    assert publish(conn, run_id) == first
    put(conn, "A", [product("A", ["blue"])], artifact_sha256="next")
    assert publish(conn, run_id) == first


async def test_v1_nested_identity_cannot_cross_catalog_cutover(conn, monkeypatch):
    from contextlib import nullcontext
    from pathlib import Path

    import psycopg
    from psycopg.types.json import Jsonb

    from suppliermcp.access import Identity
    from suppliermcp.catalog.db import migrate
    from suppliermcp.config import Settings
    from suppliermcp.search.index import rebuild_index
    from suppliermcp.service import CatalogService

    with conn.transaction():
        conn.execute("CREATE SCHEMA v1_upgrade")
        conn.execute("SET LOCAL search_path TO v1_upgrade")
        conn.execute("CREATE TABLE migrations(name text PRIMARY KEY)")
        for path in sorted(Path("migrations").glob("00[1-9]*.sql")):
            conn.execute(path.read_text())
            conn.execute("INSERT INTO migrations VALUES (%s)", (path.name,))
        # V1 silently flattened a ProductComplete nested inside ShipTo into this ordinary typed row.
        old = SourceItem(supplier="ed", source_id="7", sku="private-address", name="private-name")
        conn.execute(
            "INSERT INTO source_items VALUES (%s,%s,true,1)",
            (old.item_id, Jsonb(old.model_dump(mode="json"))),
        )
        monkeypatch.setattr("suppliermcp.service.connect", lambda settings: nullcontext(conn))
        service = CatalogService(
            Settings(), Identity("issuer", "user", "client", frozenset({"catalog:read"}))
        )
        for attempt in range(2):
            result = await service.get_product(product_id=old.item_id)
            assert result.error["code"] == "catalog_migration_required"
            assert "private-" not in result.model_dump_json()
            with pytest.raises(CatalogError) as error:
                rebuild_index(conn, None)
            assert error.value.code == "catalog_migration_required"
            if attempt == 0:
                with pytest.raises(
                    psycopg.errors.RaiseException, match="catalog_reprojection_required"
                ):
                    migrate(conn)
        assert conn.execute("SELECT data FROM source_items").fetchone()[0] == old.model_dump(
            mode="json"
        )
        assert not conn.execute("SELECT 1 FROM migrations WHERE name LIKE '011%'").fetchone()
        conn.execute("SET LOCAL search_path TO public")
        conn.execute("DROP SCHEMA v1_upgrade CASCADE")
