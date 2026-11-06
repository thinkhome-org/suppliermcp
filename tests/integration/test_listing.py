import pytest

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogError,
    CatalogQuery,
    Filter,
    Identifier,
    SourceItem,
)
from suppliermcp.search.exact import lookup
from suppliermcp.search.listing import next_page, start_listing
from suppliermcp.sync.publish import publish, stage


def seed(conn):
    rows = []
    for i in range(25):
        rows.append(
            SourceItem(
                supplier="mega",
                source_id=str(i),
                sku=f"{i:03}",
                name=f"Memory {i}",
                manufacturer="Acme",
            )
        )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain="catalog", complete=True, artifact_sha256="listing"
            ),
            rows,
        ),
    )


def test_exact_and_stable_pagination(conn):
    seed(conn)
    assert (
        lookup(conn, [Identifier(kind="sku", supplier="mega", value="001")]).entries[0]["status"]
        == "found"
    )
    assert (
        lookup(conn, [Identifier(kind="sku", supplier="mega", value="1")]).entries[0]["status"]
        == "missing"
    )
    first = start_listing(conn, CatalogQuery(), "alice")
    assert first.total == 25 and len(first.results) == 20
    conn.execute("UPDATE source_items SET data=jsonb_set(data,'{name}','\"Changed\"')")
    second = next_page(conn, first.next_cursor, "alice")
    assert len(second.results) == 5 and all(p.item.name != "Changed" for p in second.results)
    assert len({p.product_id for p in first.results + second.results}) == 25
    with pytest.raises(CatalogError, match="result_not_found"):
        next_page(conn, first.next_cursor, "bob")
    conn.execute("UPDATE query_results SET expires_at=now()-interval '1 second'")
    with pytest.raises(CatalogError, match="result_expired"):
        next_page(conn, first.next_cursor, "alice")


def test_three_valued_filter(conn):
    seed(conn)
    query = CatalogQuery(filters=[Filter(field="price", operator="lte", value=100)])
    page = start_listing(conn, query, "alice")
    assert page.total == 0 and page.unknown_total == 25
    assert (
        start_listing(conn, query.model_copy(update={"classification": "unknown"}), "alice").total
        == 25
    )


def test_invalid_field_not_ignored(conn):
    seed(conn)
    with pytest.raises(CatalogError, match="unsupported_filter"):
        start_listing(
            conn,
            CatalogQuery(
                filters=[Filter(field="anything; DROP TABLE source_items", operator="eq", value=1)]
            ),
            "alice",
        )


def test_scope_and_currency_are_validated(conn):
    from suppliermcp.search.schema import catalog_schema

    seed(conn)
    with pytest.raises(CatalogError) as error:
        catalog_schema(conn, "invented")
    assert error.value.code == "unknown_category"
    with pytest.raises(CatalogError, match="unsupported_currency"):
        start_listing(conn, CatalogQuery(sort="price_asc", currency="XYZ"), "alice")


def test_partition_boundaries_are_queryable(conn):
    seed(conn)
    query = CatalogQuery(source_id_from="mega:1", source_id_to="mega:20")
    page = start_listing(conn, query, "alice")
    assert [p.product_id for p in page.results] == [
        "mega:1",
        "mega:10",
        "mega:11",
        "mega:12",
        "mega:13",
        "mega:14",
        "mega:15",
        "mega:16",
        "mega:17",
        "mega:18",
        "mega:19",
        "mega:2",
    ]


def test_cursor_rejects_changed_query(conn):
    seed(conn)
    page = start_listing(conn, CatalogQuery(), "alice")
    with pytest.raises(CatalogError, match="result_query_mismatch"):
        next_page(conn, page.next_cursor, "alice", query_hash="changed")


def test_large_result_returns_exact_partitions(conn):
    conn.execute(
        "INSERT INTO source_items(id,data,active,revision) SELECT 'mega:'||lpad(i::text,6,'0'), '{}'::jsonb,true,1 FROM generate_series(1,100001) i"
    )
    with pytest.raises(CatalogError) as error:
        start_listing(conn, CatalogQuery(), "alice")
    import json

    assert error.value.code == "result_too_large"
    details = json.loads(error.value.message)
    assert details == {
        "count": 100001,
        "partitions": [
            {"source_id_from": "mega:000001", "source_id_to": "mega:100001"},
            {"source_id_from": "mega:100001", "source_id_to": None},
        ],
    }


def test_page_payload_budget(conn):
    seed(conn)
    conn.execute(
        "UPDATE source_items SET data=jsonb_set(data,'{name}',to_jsonb(repeat('x',150000)))"
    )
    page = start_listing(conn, CatalogQuery(), "alice")
    assert len(page.results) == 1 and page.next_cursor
    conn.execute(
        "UPDATE source_items SET data=jsonb_set(data,'{name}',to_jsonb(repeat('x',270000)))"
    )
    with pytest.raises(CatalogError) as error:
        start_listing(conn, CatalogQuery(), "alice")
    assert error.value.code == "item_too_large"


def test_explicit_numeric_mapping_and_category(conn, monkeypatch):
    from suppliermcp.catalog.contracts import Observation, SchemaRecord
    from suppliermcp.search import schema

    monkeypatch.setattr(
        schema,
        "MAPPINGS",
        {
            "native:mega:CapacityMB": {
                "field": "capacity_gb",
                "type": "number",
                "unit": "GB",
                "scale": "0.001",
            }
        },
    )
    product = SourceItem(
        supplier="mega",
        source_id="map",
        sku="map",
        name="Mapped memory",
        observations=[
            Observation(interface="mega", endpoint="base", field="CapacityMB", value="32000")
        ],
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog", artifact_sha256="mapped"),
            [product],
        ),
    )
    page = start_listing(
        conn,
        CatalogQuery(filters=[Filter(field="capacity_gb", operator="eq", value="32")]),
        "alice",
    )
    assert [p.product_id for p in page.results] == ["mega:map"]
    assert schema.catalog_schema(conn)["capacity_gb"]["unit"] == "GB"
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="ed_private", domain="schema", artifact_sha256="category"),
            [
                SchemaRecord(
                    interface="ed_private",
                    kind="ProductCategory",
                    values={"CategoryCode": "ram", "CategoryName": "Memory"},
                )
            ],
        ),
    )
    assert "price" in schema.catalog_schema(conn, "ed:ram")


def test_configured_page_and_result_limits(conn):
    from suppliermcp.config import Settings

    seed(conn)
    settings = Settings(page_size=3, max_result_rows=30, result_ttl_seconds=60)
    page = start_listing(conn, CatalogQuery(), "alice", settings=settings)
    assert len(page.results) == 3
    assert len(next_page(conn, page.next_cursor, "alice").results) == 3
    with pytest.raises(CatalogError) as error:
        start_listing(conn, CatalogQuery(), "alice", settings=Settings(max_result_rows=10))
    assert error.value.code == "result_too_large"


def test_listing_does_not_wait_for_worker_expiration_cleanup(conn):
    import psycopg

    seed(conn)
    conn.execute(
        "INSERT INTO query_results VALUES ('expired','user','old',now()-interval '1 hour','{}')"
    )
    with psycopg.connect(conn.info.dsn, password=conn.info.password) as cleaner:
        cleaner.execute("DELETE FROM query_results WHERE id='expired'")
        conn.execute("SET lock_timeout = '500ms'")
        assert start_listing(conn, CatalogQuery(), "user").total == 25


def test_order_totals_with_ties_and_missing_currency(conn):
    from suppliermcp.catalog.contracts import Offer
    from suppliermcp.config import Settings

    rows = []
    for code, unit, multiple, currency in [
        ("a", "1", 100, "CZK"),
        ("b", "2", 10, "CZK"),
        ("c", "2", 10, "CZK"),
        ("d", "0", 1, None),
        ("e", "0", 1, "EUR"),
        ("f", "1", None, "CZK"),
    ]:
        item = SourceItem(supplier="mega", source_id=code, sku=code, name=code)
        rows.extend(
            [
                item,
                Offer(
                    item_id=item.item_id,
                    unit_net=unit,
                    order_multiple=multiple,
                    currency=currency,
                    fees_net=0,
                ),
            ]
        )
    publish(
        conn,
        stage(
            conn, BatchManifest(interface="mega", domain="catalog", artifact_sha256="prices"), rows
        ),
    )
    query = CatalogQuery(sort="price_asc", currency="CZK", quantity=12)
    page = start_listing(conn, query, "alice", Settings(page_size=1))
    with pytest.raises(CatalogError, match="result_not_found"):
        next_page(conn, page.next_cursor, "bob")
    rows = list(page.results)
    while page.next_cursor:
        page = next_page(conn, page.next_cursor, "alice")
        rows.extend(page.results)
    ids = [p.product_id for p in rows]
    first = rows[0].quote
    assert (first.requested_qty, first.orderable_qty, first.total_net) == (12, 20, 40)
    assert "currency_unknown" in rows[3].quote.reasons
    assert rows[4].quote.currency == "EUR" and "currency_mismatch" in rows[4].quote.reasons
    assert rows[5].quote.orderable_qty is None and "order_multiple_unknown" in rows[5].quote.reasons
    expected = conn.execute("""
        SELECT item_id FROM current_offers ORDER BY CASE WHEN data->>'currency'='CZK'
            THEN ceil(12 / (data->>'order_multiple')::numeric) * (data->>'order_multiple')::numeric
               * ((data->>'unit_net')::numeric + (data->>'fees_net')::numeric) END NULLS LAST, item_id
    """).fetchall()
    assert ids == [row[0] for row in expected] == ["mega:" + s for s in "bcadef"]


def test_unit_price_sort_preserves_unknowns_and_missing_offers(conn):
    from suppliermcp.catalog.contracts import Offer

    seed(conn)
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="price", artifact_sha256="unit"),
            [
                Offer(item_id="mega:23", currency="CZK", unit_net=5),
                Offer(item_id="mega:24", currency="CZK", unit_net=6),
            ],
        ),
    )
    page = start_listing(conn, CatalogQuery(sort="price_desc", currency="CZK"), "alice")
    ids = [p.product_id for p in page.results + next_page(conn, page.next_cursor, "alice").results]
    assert ids == ["mega:24", "mega:23", *sorted(f"mega:{n}" for n in range(23))]


@pytest.mark.parametrize("quantity", [6, 12])
def test_listing_valuepack_quote_matches_comparison(conn, quantity):
    from suppliermcp.catalog.contracts import Offer, utcnow
    from suppliermcp.catalog.offers import quote

    item = SourceItem(supplier="mega", source_id="pack", sku="001", name="Pack")
    missing = SourceItem(supplier="mega", source_id="none", sku="002", name="No offer")
    offer = Offer(
        item_id=item.item_id,
        currency="CZK",
        unit_net=7,
        fees_net="0.50",
        order_multiple=5,
        price_rule="valuepack",
        discount_min_qty=15,
        discount=2,
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog", artifact_sha256="pack"),
            [item, missing, offer],
        ),
    )
    page = start_listing(
        conn, CatalogQuery(sort="price_asc", currency="CZK", quantity=quantity), "alice"
    )
    assert page.results[0].quote == quote(offer, quantity, utcnow())
    assert page.results[1].quote.reasons == ["offer_missing"]
    assert page.results[1].quote.evidence_at is None
