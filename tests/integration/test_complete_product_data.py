from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogQuery,
    Filter,
    Identifier,
    Observation,
    SchemaRecord,
    SourceItem,
)
from suppliermcp.search.exact import lookup
from suppliermcp.search.listing import matching_ids
from suppliermcp.search.schema import catalog_schema
from suppliermcp.sync.publish import publish, stage


def seed(conn):
    observations = [
        Observation(
            interface="mega",
            endpoint="params",
            field="parameter:42",
            value=v,
            value_key=v,
            cardinality="many",
        )
        for v in ["red", "blue"]
    ]
    observations += [
        Observation(interface="mega", endpoint="base", field="EAN2", value="0012345678901")
    ]
    rows = [
        SourceItem(
            supplier="mega", source_id="1", sku="0001", name="Memory", observations=observations
        ),
        SourceItem(supplier="mega", source_id="2", sku="0002", name="Unknown"),
        SchemaRecord(
            interface="mega",
            kind="parameter",
            values={"code": "42", "label": "Color", "cardinality": "many"},
        ),
        SchemaRecord(interface="mega", kind="SCategorySys", values={"Id": "7", "Name": "Memory"}),
    ]
    publish(
        conn, stage(conn, BatchManifest(interface="mega", domain="catalog", endpoint="base"), rows)
    )


def test_multivalued_filter_membership_and_unknown(conn):
    seed(conn)
    for color in ["red", "blue"]:
        yes, unknown = matching_ids(
            conn,
            CatalogQuery(
                filters=[Filter(field="native:mega:parameter:42", operator="eq", value=color)]
            ),
        )
        assert yes == ["mega:1"] and unknown == ["mega:2"]
    yes, unknown = matching_ids(
        conn,
        CatalogQuery(
            filters=[Filter(field="native:mega:parameter:42", operator="eq", value="green")]
        ),
    )
    assert yes == [] and unknown == ["mega:2"]


def test_native_schema_labels_and_source_category(conn):
    seed(conn)
    schema = catalog_schema(conn, category="mega:7")
    assert schema["native:mega:parameter:42"]["label"] == "Color"
    assert schema["native:mega:parameter:42"]["cardinality"] == "many"


def test_alternate_ean_preserves_leading_zeros(conn):
    seed(conn)
    assert (
        lookup(conn, [Identifier(kind="ean", value="0012345678901")]).entries[0]["status"]
        == "found"
    )
    assert (
        lookup(conn, [Identifier(kind="ean", value="12345678901")]).entries[0]["status"]
        == "missing"
    )


def test_conflicting_single_value_remains_unknown(conn):
    facts = [
        Observation(interface="mega", endpoint=e, field="size", value=v)
        for e, v in [("a", "10"), ("b", "20")]
    ]
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog"),
            [SourceItem(supplier="mega", source_id="1", sku="1", name="X", observations=facts)],
        ),
    )
    yes, unknown = matching_ids(
        conn, CatalogQuery(filters=[Filter(field="native:mega:size", operator="eq", value="10")])
    )
    assert yes == [] and unknown == ["mega:1"]


def test_verified_native_numeric_type_supports_range(conn):
    facts = [
        Observation(
            interface="mega",
            endpoint="params",
            field="parameter:9:measure",
            value="32",
            value_type="number",
            unit="GB",
        )
    ]
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog"),
            [
                SourceItem(
                    supplier="mega", source_id="1", sku="1", name="Memory", observations=facts
                )
            ],
        ),
    )
    field = "native:mega:parameter:9:measure"
    yes, unknown = matching_ids(
        conn, CatalogQuery(filters=[Filter(field=field, operator="gte", value=16)])
    )
    assert yes == ["mega:1"] and unknown == []
    assert catalog_schema(conn)[field]["type"] == "number"


def test_index_contains_parameter_labels_and_relationships(conn):
    from suppliermcp.search.index import document

    seed(conn)
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="schema", endpoint="relations"),
            [
                SchemaRecord(
                    interface="mega",
                    kind="relationship",
                    values={
                        "item_id": "mega:1",
                        "target_id": "mega:2",
                        "kind": "accessory",
                        "name": "Compatible adapter",
                    },
                )
            ],
        ),
    )
    text = document(("mega:1", {}, 1), conn=conn)["text"]
    assert "color" in text and "compatible adapter" in text


def test_multivalued_native_survives_installed_common_mapping(conn, monkeypatch):
    from suppliermcp.search import schema

    monkeypatch.setattr(
        schema, "MAPPINGS", {"native:mega:EAN2": {"field": "alternate_identifier", "type": "text"}}
    )
    seed(conn)
    yes, _ = matching_ids(
        conn,
        CatalogQuery(
            filters=[Filter(field="native:mega:parameter:42", operator="eq", value="blue")]
        ),
    )
    assert yes == ["mega:1"]


def test_sku_only_enrichment_rejects_ambiguous_identity(conn):
    import pytest

    from suppliermcp.catalog.contracts import CatalogError

    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog"),
            [
                SourceItem(supplier="mega", source_id=str(i), sku="shared", name="Product")
                for i in [1, 2]
            ],
        ),
    )
    with pytest.raises(CatalogError, match="unresolved_product_reference"):
        stage(
            conn,
            BatchManifest(interface="mega", domain="schema"),
            [
                SchemaRecord(
                    interface="mega",
                    kind="product_facts",
                    values={"supplier": "mega", "sku": "shared", "observations": []},
                )
            ],
        )


def test_source_category_filter_and_dictionary_search_name(conn):
    from suppliermcp.search.index import document

    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog", endpoint="base"),
            [
                SourceItem(
                    supplier="mega",
                    source_id="1",
                    sku="1",
                    name="X",
                    observations=[
                        Observation(interface="mega", endpoint="base", field="ScaId", value="7")
                    ],
                )
            ],
        ),
    )
    conn.execute("UPDATE index_outbox SET done=true")
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="schema", endpoint="SCategorySys"),
            [
                SchemaRecord(
                    interface="mega",
                    kind="SCategorySys",
                    values={"Id": "7", "Name": "Memory modules"},
                )
            ],
        ),
    )
    assert matching_ids(
        conn, CatalogQuery(filters=[Filter(field="category", operator="eq", value="mega:7")])
    )[0] == ["mega:1"]
    assert "memory modules" in document(("mega:1", {}, 1), conn=conn)["text"]
    assert conn.execute("SELECT 1 FROM index_outbox WHERE item_id='mega:1' AND NOT done").fetchone()


def test_large_incompressible_supplier_description_is_publishable(conn):
    import random

    from suppliermcp.catalog.repository import get_product

    text = random.Random(42).randbytes(12000).hex()
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="ed_public", domain="catalog"),
            [
                SourceItem(
                    supplier="ed",
                    source_id="large",
                    sku="large",
                    name="Product",
                    observations=[
                        Observation(
                            interface="ed_public",
                            endpoint="catalog",
                            field="Description",
                            value=text,
                        )
                    ],
                )
            ],
        ),
    )
    assert get_product(conn, "ed:large").item.observations[0].value == text
