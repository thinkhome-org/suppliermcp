from datetime import timedelta
from xml.etree.ElementTree import fromstring

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogQuery,
    Filter,
    Observation,
    Offer,
    SchemaRecord,
    SourceItem,
    utcnow,
)
from suppliermcp.catalog.repository import get_product
from suppliermcp.search.index import document
from suppliermcp.search.listing import matching_ids
from suppliermcp.suppliers.mega.exports import normalize_record
from suppliermcp.sync.publish import publish, stage


def put(conn, endpoint, rows, **kwargs):
    return publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain=kwargs.pop("domain", "schema"), endpoint=endpoint, **kwargs
            ),
            rows,
        ),
    )


def seed(conn):
    put(
        conn,
        "base",
        [
            SourceItem(supplier="mega", source_id=str(i), sku="00" + str(i), name="Product")
            for i in [1, 2]
        ],
        domain="catalog",
    )


def test_empty_targeted_replacement_removes_only_requested_item(conn):
    seed(conn)
    for endpoint in ["params", "other"]:
        put(
            conn,
            endpoint,
            [
                SchemaRecord(
                    interface="mega",
                    kind="product_facts",
                    values={
                        "item_id": "mega:" + str(i),
                        "observations": [
                            Observation(
                                interface="mega", endpoint=endpoint, field="color", value="red"
                            ).model_dump(mode="json")
                        ],
                    },
                )
                for i in [1, 2]
            ]
            + [
                SchemaRecord(
                    interface="mega",
                    kind="relationship",
                    values={"item_id": "mega:1", "target_id": "mega:2", "kind": "accessory"},
                )
            ],
        )
    put(conn, "params", [], mode="targeted", replace_scope="items", requested_skus=["001"])
    assert {o.endpoint for o in get_product(conn, "mega:1").item.observations} == {"other"}
    assert {o.endpoint for o in get_product(conn, "mega:2").item.observations} == {
        "params",
        "other",
    }
    assert conn.execute("SELECT endpoint FROM relationships WHERE item_id='mega:1'").fetchall() == [
        ("other",)
    ]


def test_scalar_and_many_declarations_do_not_certify_conflict(conn):
    seed(conn)
    put(
        conn,
        "base",
        [
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={
                    "item_id": "mega:1",
                    "observations": [
                        Observation(
                            interface="mega", endpoint="base", field="Name", value="First"
                        ).model_dump(mode="json")
                    ],
                },
            )
        ],
    )
    manifest = BatchManifest(interface="mega", domain="schema", endpoint="extra")
    put(
        conn,
        "extra",
        normalize_record(manifest, fromstring('<StoItem Id="1" Code="001" Name="Second"/>')),
    )
    yes, unknown = matching_ids(
        conn, CatalogQuery(filters=[Filter(field="native:mega:Name", operator="eq", value="First")])
    )
    assert not yes and "mega:1" in unknown
    assert {
        o.value for o in get_product(conn, "mega:1").item.observations if o.field == "Name"
    } == {"First", "Second"}


def test_unchanged_success_clears_only_covered_failure_without_reaging(conn):
    seed(conn)
    evidence = utcnow() - timedelta(days=1)
    for endpoint in ["price", "other"]:
        put(
            conn,
            endpoint,
            [Offer(item_id="mega:1", unit_net="10", evidence_at=evidence)],
            domain="price",
            artifact_sha256=endpoint,
        )
    conn.execute("UPDATE current_offers SET data=jsonb_set(data,'{refresh_failed}','true')")
    put(
        conn,
        "price",
        [Offer(item_id="mega:1", unit_net="10", evidence_at=utcnow())],
        domain="price",
        artifact_sha256="price",
    )
    rows = dict(conn.execute("SELECT endpoint,data FROM current_offers WHERE item_id='mega:1'"))
    assert rows["price"]["refresh_failed"] is False and rows["other"]["refresh_failed"] is True
    assert Offer.model_validate(rows["price"]).evidence_at == evidence


def test_removed_category_dictionary_invalidates_index(conn):
    seed(conn)
    put(
        conn,
        "base",
        [
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={
                    "item_id": "mega:1",
                    "observations": [
                        Observation(
                            interface="mega", endpoint="base", field="ScaId", value="7"
                        ).model_dump(mode="json")
                    ],
                },
            )
        ],
    )
    put(
        conn,
        "SCategorySys",
        [
            SchemaRecord(
                interface="mega",
                kind="SCategorySys",
                values={"Id": "7", "Name": "ObsoleteCategory"},
            )
        ],
        replace_scope="endpoint",
    )
    conn.execute("UPDATE index_outbox SET done=true")
    put(conn, "SCategorySys", [], replace_scope="endpoint")
    assert "obsoletecategory" not in document(("mega:1", {}, 1), conn=conn)["text"]
    assert conn.execute("SELECT 1 FROM index_outbox WHERE item_id='mega:1' AND NOT done").fetchone()


def test_removed_parameter_definition_invalidates_index(conn):
    seed(conn)
    put(
        conn,
        "facts",
        [
            SchemaRecord(
                interface="mega",
                kind="product_facts",
                values={
                    "item_id": "mega:1",
                    "observations": [
                        Observation(
                            interface="mega", endpoint="facts", field="parameter:7", value="red"
                        ).model_dump(mode="json")
                    ],
                },
            )
        ],
    )
    rows = [
        SchemaRecord(
            interface="mega", kind="parameter", values={"code": str(i), "label": "Label" + str(i)}
        )
        for i in [7, 8]
    ]
    put(conn, "definitions", rows, replace_scope="endpoint")
    conn.execute("UPDATE index_outbox SET done=true")
    put(conn, "definitions", rows[1:], replace_scope="endpoint")
    assert conn.execute("SELECT 1 FROM index_outbox WHERE item_id='mega:1' AND NOT done").fetchone()
