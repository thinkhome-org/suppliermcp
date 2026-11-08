from datetime import timedelta
from decimal import Decimal

import pytest

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogQuery,
    Observation,
    Offer,
    SourceItem,
    utcnow,
)
from suppliermcp.catalog.repository import get_product
from suppliermcp.search.index import document
from suppliermcp.search.listing import start_listing
from suppliermcp.sync.jobs import run_refresh
from suppliermcp.sync.publish import publish, stage


def publish_rows(conn, when, checksum, rows, domain="catalog", complete=False, stock_only=False):
    return publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega",
                domain=domain,
                started_at=when,
                artifact_sha256=checksum,
                complete=complete,
                stock_only=stock_only,
            ),
            rows,
        ),
    )


def item(id="1", observations=None):
    return SourceItem(
        supplier="mega", source_id=id, sku=id, name="Product", observations=observations or []
    )


def test_unchanged_fence_and_terminal_staging_cleanup(conn):
    t = utcnow()
    original = [item(), Offer(item_id="mega:1", unit_net="10", evidence_at=t)]
    publish_rows(conn, t, "A", original)
    publish_rows(conn, t + timedelta(minutes=20), "A", original)
    publish_rows(
        conn, t + timedelta(minutes=10), "B", [item(), Offer(item_id="mega:1", unit_net="20")]
    )
    assert get_product(conn, "mega:1").offers[0].unit_net == 10
    assert get_product(conn, "mega:1").offers[0].evidence_at == t
    assert conn.execute("SELECT count(*) FROM staging").fetchone()[0] == 0
    assert conn.execute("SELECT started_at FROM domain_checkpoints").fetchone()[0] == t + timedelta(
        minutes=20
    )


def test_absent_stock_has_independent_new_evidence(conn):
    t = utcnow()
    publish_rows(conn, t, "base", [item(), item("2")], complete=True)
    publish_rows(
        conn,
        t + timedelta(minutes=10),
        "stock1",
        [
            item(),
            Offer(
                item_id="mega:1",
                stock_state="in_stock",
                stock_qty="5",
                evidence_at=t + timedelta(minutes=10),
            ),
        ],
        domain="stock",
    )
    publish_rows(
        conn,
        t + timedelta(minutes=20),
        "catalog2",
        [
            item(),
            Offer(
                item_id="mega:1",
                unit_net="25",
                stock_state="in_stock",
                stock_qty="3",
                evidence_at=t + timedelta(minutes=20),
            ),
        ],
    )
    publish_rows(
        conn,
        t + timedelta(minutes=30),
        "stock2",
        [item("2")],
        domain="stock",
        complete=True,
        stock_only=True,
    )
    offer = get_product(conn, "mega:1").offers[0]
    assert offer.stock_state == "out_of_stock" and offer.stock_qty == 0
    assert offer.unit_net == 25 and offer.evidence_at == t + timedelta(minutes=20)
    publish_rows(
        conn,
        t + timedelta(minutes=40),
        "stock3",
        [
            item(),
            Offer(
                item_id="mega:1",
                stock_state="in_stock",
                stock_qty="2",
                evidence_at=t + timedelta(minutes=40),
            ),
        ],
        domain="stock",
    )
    returned = get_product(conn, "mega:1").offers[0]
    assert returned.stock_state == "in_stock" and returned.stock_qty == 2
    assert returned.evidence_at == t + timedelta(minutes=20)


def test_partial_catalog_cannot_become_complete_from_stock(conn):
    class Adapter:
        interface = "mega"
        store = None

        def fetch(self, domain, codes):
            return BatchManifest(
                interface="mega", domain=domain, artifact_sha256=domain, complete=False
            )

        def parse(self, manifest):
            yield item()

    run_refresh(conn, Adapter(), "catalog")
    run_refresh(conn, Adapter(), "stock")
    assert start_listing(conn, CatalogQuery(), "alice").coverage.complete is False


def test_index_preserves_accumulated_description(conn):
    t = utcnow()
    publish_rows(
        conn,
        t,
        "base",
        [
            item(
                observations=[
                    Observation(
                        interface="mega",
                        endpoint="base",
                        field="Description",
                        value="enterprise archiving",
                    )
                ]
            )
        ],
    )
    publish_rows(
        conn,
        t + timedelta(minutes=1),
        "stock",
        [
            item(
                observations=[
                    Observation(interface="mega", endpoint="stock", field="QtyFree", value="5")
                ]
            )
        ],
        domain="stock",
    )
    row = conn.execute("SELECT id,data,revision FROM source_items WHERE id='mega:1'").fetchone()
    assert "enterprise archiving" in document(row, conn=conn)["text"]


def test_verified_pack_mapping_reaches_matching(conn, monkeypatch):
    from suppliermcp.catalog.matching import match_items
    from suppliermcp.search import schema

    monkeypatch.setattr(
        schema, "MAPPINGS", {"native:mega:VerifiedPack": {"field": "pack_count", "type": "number"}}
    )
    for id in ["1", "2"]:
        product = item(
            id, [Observation(interface="mega", endpoint="base", field="VerifiedPack", value="1")]
        ).model_copy(update={"manufacturer": "Maker", "mpn": "PART"})
        publish_rows(conn, utcnow(), id, [product])
    assert (
        match_items(get_product(conn, "mega:1").item, get_product(conn, "mega:2").item).verdict
        == "same"
    )


def test_index_bulk_acknowledges_individual_results(conn):
    from suppliermcp.search.index import drain_outbox

    publish_rows(conn, utcnow(), "bulk", [item("1"), item("2")])

    class Client:
        calls = []

        def import_documents(self, collection, documents):
            self.calls.append(documents)
            return [d["id"] == "mega:1" for d in documents]

    client = Client()
    assert drain_outbox(conn, client) == 1
    assert len(client.calls) == 1 and len(client.calls[0]) == 2
    assert conn.execute("SELECT item_id FROM index_outbox WHERE NOT done").fetchall() == [
        ("mega:2",)
    ]


@pytest.mark.parametrize("interface", ["mega", "ed_public"])
def test_verified_offer_contract_through_parser_and_publication(conn, tmp_path, interface):
    from suppliermcp.catalog.offers import compare
    from suppliermcp.suppliers.ed.public import EdPublicAdapter
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    t = utcnow()
    contract = {
        "order_multiple": "1",
        "fees_net": "0",
        "currency": "CZK",
        "timestamp_field": "PriceUpdatedAt",
        "timestamp_is_price_evidence": True,
        "freshness_seconds": 3600,
    }
    path = tmp_path / "offer.xml"
    if interface == "mega":
        path.write_text(
            f'<Result><StoItem Id="1" Code="1" PriceDea="10" PriceUpdatedAt="{t.isoformat()}"/></Result>'
        )
        adapter = MegaAdapter(contracts={"StoItemBase": {"offer": contract}})
        endpoint = "StoItemBase"
        product_id = "mega:1"
    else:
        path.write_text(
            f"<ProductList><Product><ProId>1</ProId><Code>1</Code><YourPrice>10</YourPrice><PriceUpdatedAt>{t.isoformat()}</PriceUpdatedAt></Product></ProductList>"
        )
        adapter = EdPublicAdapter()
        adapter.offer_contract = contract
        endpoint = "getProductList"
        product_id = "ed:1"
    manifest = BatchManifest(
        interface=interface,
        domain="catalog",
        endpoint=endpoint,
        path=str(path),
        artifact_sha256=interface,
    )
    publish(conn, stage(conn, manifest, adapter.parse(manifest)))
    result = compare(get_product(conn, product_id).offers, Decimal(7), utcnow())
    assert result.offers[0].total_net == 70 and result.fresh_winner == product_id


def test_index_worker_drains_more_than_one_batch(conn):
    from suppliermcp.search.index import drain_pending

    publish_rows(conn, utcnow(), "many", [item(str(i)) for i in range(251)])

    class Client:
        calls = []

        def import_documents(self, collection, documents):
            self.calls.append(len(documents))
            return [True] * len(documents)

    client = Client()
    assert drain_pending(conn, client) == 251
    assert client.calls == [200, 51]
    assert conn.execute("SELECT count(*) FROM index_outbox WHERE NOT done").fetchone()[0] == 0


def test_catalog_coverage_requires_every_configured_interface(conn):
    from pydantic import SecretStr

    from suppliermcp.config import Settings

    class Adapter:
        interface = "mega"
        store = None

        def fetch(self, domain, codes):
            return BatchManifest(
                interface="mega", domain=domain, artifact_sha256="full", complete=True
            )

        def parse(self, manifest):
            yield item()

    run_refresh(conn, Adapter(), "catalog")
    credentials = {"mega": (SecretStr("a"), SecretStr("b"))}
    assert start_listing(
        conn, CatalogQuery(), "alice", settings=Settings(credentials=credentials)
    ).coverage.complete
    credentials["ed_public"] = (SecretStr("a"), SecretStr("b"))
    result = start_listing(
        conn, CatalogQuery(), "alice", settings=Settings(credentials=credentials)
    )
    assert (
        not result.coverage.complete
        and result.coverage.interfaces["ed_public"]["outcome"] == "not_fetched"
    )


def test_stock_refresh_does_not_replace_price_rule_or_freshness(conn):
    from suppliermcp.catalog.offers import compare

    t = utcnow()
    publish_rows(
        conn,
        t,
        "price-evidence",
        [
            item(),
            Offer(
                item_id="mega:1",
                unit_net="10",
                fees_net="0",
                currency="CZK",
                order_multiple="1",
                price_rule="valuepack",
                discount_min_qty="10",
                source_updated_at=t,
                freshness_seconds=3600,
                evidence_at=t,
            ),
        ],
    )
    publish_rows(
        conn,
        t + timedelta(seconds=1),
        "stock-evidence",
        [
            item(),
            Offer(
                item_id="mega:1",
                stock_state="in_stock",
                stock_qty="100",
                evidence_at=t + timedelta(seconds=1),
            ),
        ],
        domain="stock",
    )
    offers = get_product(conn, "mega:1").offers
    assert offers[0].price_rule == "valuepack"
    assert compare(offers, Decimal(1), utcnow()).offers[0].total_net is None
    assert compare(offers, Decimal(10), utcnow()).fresh_winner == "mega:1"
