from suppliermcp.catalog.contracts import CatalogError, LookupResult
from suppliermcp.catalog.repository import get_products, read_status


def lookup(conn, identifiers):
    if not 1 <= len(identifiers) <= 50:
        raise CatalogError("batch_limit")
    if not conn.execute("SELECT 1 FROM source_items LIMIT 1").fetchone():
        raise CatalogError("catalog_not_populated")
    entries = []
    for identifier in identifiers:
        field = {"sku": "sku", "mpn": "mpn", "ean": "ean"}[identifier.kind]
        query = "SELECT id FROM source_items WHERE active AND data->>%s=%s"
        params = [field, identifier.value]
        if identifier.kind == "ean":
            query = "SELECT id FROM source_items s WHERE active AND (data->>%s=%s OR EXISTS(SELECT 1 FROM catalog_values v WHERE v.item_id=s.id AND v.state='known' AND md5(v.value)=md5(%s) AND v.value=%s AND v.field=ANY(%s)))"
            params += [
                identifier.value,
                identifier.value,
                [
                    "native:mega:EAN",
                    "native:mega:EAN2",
                    "native:mega:Row.StiEAN",
                    "native:mega:Row.StiEAN2",
                    "native:ed_public:EANCode",
                    "native:ed_private:EANCode",
                ],
            ]
        if identifier.supplier:
            query += " AND data->>'supplier'=%s"
            params.append(identifier.supplier)
        if identifier.kind == "mpn":
            query += " AND lower(data->>'manufacturer')=lower(%s)"
            params.append(identifier.manufacturer)
        ids = [r[0] for r in conn.execute(query, params)]
        entries.append(
            {
                "identifier": identifier.model_dump(),
                "status": "found" if len(ids) == 1 else "ambiguous" if ids else "missing",
                "products": [
                    p.model_dump(mode="json")
                    for p in get_products(conn, ids, include_evidence=False)
                ],
            }
        )
    return LookupResult(entries=entries, coverage=read_status(conn))
