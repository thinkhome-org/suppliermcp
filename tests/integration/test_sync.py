from datetime import timedelta
from decimal import Decimal

import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, Offer, SourceItem, utcnow
from suppliermcp.catalog.repository import get_product
from suppliermcp.sync.publish import publish, stage


def load(
    conn,
    *,
    count=4,
    when=None,
    mode="full",
    domain="catalog",
    complete=True,
    checksum="a",
    stock_only=False,
):
    m = BatchManifest(
        interface="mega",
        domain=domain,
        mode=mode,
        complete=complete,
        started_at=when or utcnow(),
        artifact_sha256=checksum,
        stock_only=stock_only,
    )
    rows = []
    for i in range(count):
        rows += [
            SourceItem(supplier="mega", source_id=str(i), sku=f"00{i}", name=f"Item {i}"),
            Offer(
                item_id=f"mega:{i}",
                unit_net="10",
                stock_qty="5",
                stock_state="in_stock",
                evidence_at=m.started_at,
            ),
        ]
    return stage(conn, m, iter(rows))


def test_replay_and_older_run(conn):
    t = utcnow()
    r = load(conn, when=t)
    rev = publish(conn, r)
    assert publish(conn, r) == rev
    old = load(conn, when=t - timedelta(hours=1), checksum="b")
    assert publish(conn, old) == rev
    assert conn.execute("SELECT count(*) FROM source_items WHERE active").fetchone()[0] == 4
    assert conn.execute("SELECT count(*) FROM index_outbox").fetchone()[0] == 4


def test_suspicious_drop_and_failed_staging_preserve_catalog(conn):
    publish(conn, load(conn))
    before = get_product(conn, "mega:0")
    with pytest.raises(CatalogError, match="import_quarantined"):
        publish(conn, load(conn, count=1, checksum="b"))

    def broken():
        yield SourceItem(supplier="mega", source_id="x", sku="x", name="x")
        raise CatalogError("invalid_export")

    with pytest.raises(CatalogError):
        stage(conn, BatchManifest(interface="mega", domain="catalog"), broken())
    assert get_product(conn, "mega:0") == before
    assert conn.execute("SELECT count(*) FROM source_items WHERE active").fetchone()[0] == 4


def test_full_stock_absence_vs_delta(conn):
    publish(conn, load(conn))
    publish(conn, load(conn, count=1, domain="stock", checksum="stock", stock_only=True))
    assert get_product(conn, "mega:3").offers[0].stock_qty == Decimal(0)
    publish(conn, load(conn, count=4, domain="stock", checksum="stock2", stock_only=True))
    publish(
        conn, load(conn, count=1, domain="stock", mode="delta", checksum="delta", stock_only=True)
    )
    assert get_product(conn, "mega:3").offers[0].stock_qty == Decimal(5)


def test_identical_hash_keeps_evidence(conn):
    t = utcnow()
    publish(conn, load(conn, when=t))
    before = get_product(conn, "mega:0").offers[0].evidence_at
    publish(conn, load(conn, when=t + timedelta(hours=1)))
    assert get_product(conn, "mega:0").offers[0].evidence_at == before


def test_empty_full_snapshot_quarantined(conn):
    publish(conn, load(conn))
    with pytest.raises(CatalogError, match="import_quarantined"):
        publish(conn, load(conn, count=0, checksum="empty"))


def test_incomplete_interface_does_not_hide_other_ed_items(conn):
    a = BatchManifest(
        interface="ed_private", domain="catalog", complete=True, artifact_sha256="private"
    )
    publish(
        conn,
        stage(
            conn,
            a,
            [
                SourceItem(supplier="ed", source_id="1", sku="1", name="A"),
                SourceItem(supplier="ed", source_id="2", sku="2", name="B"),
            ],
        ),
    )
    b = BatchManifest(
        interface="ed_public", domain="catalog", complete=True, artifact_sha256="public"
    )
    publish(conn, stage(conn, b, [SourceItem(supplier="ed", source_id="1", sku="1", name="A")]))
    assert get_product(conn, "ed:2").item.name == "B"


def test_soap_gateway_sends_only_allowed_reads():
    from suppliermcp.suppliers.ed.gateway import EdGateway

    class Transport:
        def read(self, method, url, **kwargs):
            assert method == "POST"
            assert kwargs["endpoint"] == "getProductDetail"
            assert b"<code>001</code>" in kwargs["body"]
            assert b"http://www.elinkx.cz" in kwargs["body"]
            return b"<Response/>"

    g = EdGateway(Transport(), "https://example/service.asmx", "login", "password")
    assert g.call("getProductDetail", code="001") == b"<Response/>"
    with pytest.raises(CatalogError, match="operation_not_allowed"):
        g.call("createNewOrder")
