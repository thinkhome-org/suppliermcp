import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.catalog.repository import get_products
from suppliermcp.sync.lifecycle import check_abort

MAPPINGS = json.loads((Path(__file__).parents[1] / "catalog/mappings.json").read_text())

BASE = {
    "supplier": "text",
    "category": "text",
    "manufacturer": "text",
    "sku": "text",
    "ean": "text",
    "mpn": "text",
    "price": "number",
    "currency": "text",
    "stock_state": "text",
    "stock_qty": "number",
}


def catalog_schema(conn, category=None):
    if (
        category is not None
        and not conn.execute(
            "SELECT 1 FROM source_schema WHERE (kind='ProductCategory' AND 'ed:' || (data->>'CategoryCode')=%s) OR (kind IN ('SCategorySys','SPresentTree') AND 'mega:' || (data->>'Id')=%s) LIMIT 1",
            (category, category),
        ).fetchone()
    ):
        raise CatalogError(
            "unknown_category", "No verified category mapping is installed for this category"
        )
    types = dict(BASE)
    types.update(dict(conn.execute("SELECT DISTINCT field,value_type FROM catalog_values")))
    result = {
        field: {
            "type": kind,
            "operators": ["eq", "in", "gte", "lte"] if kind == "number" else ["eq", "in"],
        }
        for field, kind in sorted(types.items())
    }

    for (definition,) in conn.execute("SELECT data FROM source_schema WHERE kind='parameter'"):
        field = "native:mega:parameter:" + definition["code"]
        if field in result:
            result[field].update(
                label=definition["label"], cardinality=definition.get("cardinality", "many")
            )
    for native, mapping in MAPPINGS.items():
        field = mapping["field"]
        if field in result:
            result[field]["unit"] = mapping.get("unit")
            result[field]["source_field"] = native
    return result


def validate_filter(f, schema):
    meta = schema.get(f.field)
    if not meta or f.operator not in meta["operators"]:
        raise CatalogError("unsupported_filter")
    values = f.value if f.operator == "in" else [f.value]
    if not isinstance(values, list) or not values:
        raise CatalogError("invalid_filter_value")
    for value in values:
        if meta["type"] == "number":
            try:
                if isinstance(value, bool) or not Decimal(str(value)).is_finite():
                    raise ValueError()
            except (ValueError, InvalidOperation):
                raise CatalogError("invalid_filter_value") from None
        elif not isinstance(value, str):
            raise CatalogError("invalid_filter_value")
    return f


def refresh_values(conn, item_ids):
    ids = list(item_ids)
    for start in range(0, len(ids), 200):
        check_abort()
        batch = ids[start : start + 200]
        views = get_products(conn, batch)
        conn.execute("DELETE FROM catalog_values WHERE item_id=ANY(%s)", (batch,))
        with conn.cursor().copy(
            "COPY catalog_values (item_id,field,value,state,value_type,value_key) FROM STDIN"
        ) as copy:
            for view in views:
                for row in _value_rows(view):
                    check_abort()
                    copy.write_row(row)


def _value_rows(view):
    item_id = view.product_id
    values = {
        f: (getattr(view.item, f), "text")
        for f in ["supplier", "manufacturer", "sku", "ean", "mpn"]
    }
    offer = view.offers[0] if view.offers else None
    for f, source, kind in [
        ("price", "unit_net", "number"),
        ("currency", "currency", "text"),
        ("stock_state", "stock_state", "text"),
        ("stock_qty", "stock_qty", "number"),
    ]:
        values[f] = (getattr(offer, source) if offer else None, kind)
    native = {}
    native_types = {}
    many = set()
    scalar = set()
    conflicted = set()
    for o in view.item.observations:
        if o.derivation == "mapped":
            continue
        field = f"native:{o.interface}:{o.field}"
        native.setdefault(field, set())
        native_types.setdefault(field, set()).add(o.value_type)
        if o.cardinality == "many":
            many.add(field)
        else:
            scalar.add(field)
        if o.state == "conflict":
            conflicted.add(field)
        if o.state == "known" and isinstance(o.value, (str, int, float)):
            value = str(o.value)
            if o.value_type == "number":
                try:
                    if not Decimal(value).is_finite():
                        raise InvalidOperation()
                except InvalidOperation:
                    conflicted.add(field)
                    continue
            native[field].add(value)
    conflicted.update(many & scalar)
    categories = {"mega:" + value for value in native.get("native:mega:ScaId", set())}
    if categories:
        native["category"] = categories
        native_types["category"] = {"text"}
        many.add("category")
    for field, entries in native.items():
        if len(native_types[field]) != 1:
            conflicted.add(field)
        values[field] = (
            next(iter(entries)) if len(entries) == 1 and field not in conflicted else None,
            "number" if native_types[field] == {"number"} else "text",
        )
    mapped = {}
    for native_field, mapping in MAPPINGS.items():
        value = values.get(native_field, (None, "text"))[0]
        if mapping.get("type") not in {"text", "number"} or mapping["field"] in BASE:
            raise CatalogError("invalid_mapping")
        if value is not None and mapping["type"] == "number":
            try:
                value = Decimal(value) * Decimal(mapping.get("scale", "1"))
                if not value.is_finite():
                    value = None
            except InvalidOperation:
                value = None
        mapped.setdefault(mapping["field"], []).append((value, mapping["type"]))
    for field, entries in mapped.items():
        known = {str(v) for v, _ in entries if v is not None}
        values[field] = (next(iter(known)) if len(known) == 1 else None, entries[0][1])
    for field, (value, kind) in values.items():
        entries = sorted(native[field]) if field in many and field not in conflicted else [value]
        for index, entry in enumerate(entries or [None]):
            state = "known" if entry is not None and entry != "unknown" else "unknown"
            yield (
                item_id,
                field,
                str(entry) if entry is not None else None,
                state,
                kind,
                str(index),
            )


def mapped_observations(observations):
    """Preserve supplier provenance while exposing only explicitly verified common facts."""
    result = []
    for observation in observations:
        mapping = MAPPINGS.get(f"native:{observation.interface}:{observation.field}")
        if not mapping or observation.derivation == "mapped":
            continue
        value, state = observation.value, observation.state
        if state == "known" and mapping.get("type") == "number":
            try:
                number = Decimal(str(value)) * Decimal(mapping.get("scale", "1"))
                if not number.is_finite():
                    raise InvalidOperation()
                value = str(number.normalize())
            except InvalidOperation:
                value, state = None, "missing"
        result.append(
            observation.model_copy(
                update={
                    "field": mapping["field"],
                    "value": value,
                    "state": state,
                    "unit": mapping.get("unit"),
                    "derivation": "mapped",
                }
            )
        )
    for field in {o.field for o in result}:
        values = {str(o.value) for o in result if o.field == field and o.state == "known"}
        if len(values) > 1 or any(o.field == field and o.state == "conflict" for o in result):
            for o in result:
                if o.field == field:
                    o.state = "conflict"
    return result


def catalog_schema_page(conn, category, cursor, principal, settings):
    """Keep the legacy field map; reserve _continuation for large schema snapshots."""
    import secrets
    from datetime import timedelta

    from psycopg.types.json import Jsonb

    from suppliermcp.catalog.contracts import utcnow

    if cursor:
        if category is not None:
            raise CatalogError("result_query_mismatch")
        row = conn.execute(
            "SELECT r.id,r.principal,r.expires_at,r.data,c.offset_value FROM query_cursors c JOIN query_results r ON r.id=c.result_id WHERE c.id=%s",
            (cursor,),
        ).fetchone()
        if not row or row[1] != principal:
            raise CatalogError("result_not_found")
        result_id, _, expires, data, offset = row
        if expires <= utcnow():
            raise CatalogError("result_expired")
        if data.get("kind") == "dictionary":
            from suppliermcp.mcp.details import _next

            return _next(conn, cursor, principal, expected_kind="dictionary")
        if data.get("kind") != "schema":
            raise CatalogError("result_query_mismatch")
    else:
        schema = catalog_schema(conn, category)
        if len(json.dumps(schema).encode()) <= settings.max_response_bytes:
            return schema
        result_id = secrets.token_urlsafe(24)
        expires = utcnow() + timedelta(seconds=settings.result_ttl_seconds)
        data = {
            "kind": "schema",
            "count": len(schema),
            "max_response_bytes": settings.max_response_bytes,
        }
        offset = 0
        with conn.transaction():
            conn.execute(
                "INSERT INTO query_results VALUES (%s,%s,%s,%s,%s)",
                (result_id, principal, "schema", expires, Jsonb(data)),
            )
            with conn.cursor().copy(
                "COPY query_result_rows (result_id,ordinal,data) FROM STDIN"
            ) as copy:
                for i, (field, meta) in enumerate(sorted(schema.items())):
                    copy.write_row((result_id, i, Jsonb({field: meta})))
    continuation = secrets.token_urlsafe(24)
    page = {
        "_continuation": {
            "next_cursor": continuation,
            "snapshot_id": result_id,
            "expires_at": expires.isoformat(),
        }
    }
    count = 0
    with conn.transaction(), conn.cursor(name="schema_page") as rows:
        rows.execute(
            "SELECT data FROM query_result_rows WHERE result_id=%s AND ordinal>=%s ORDER BY ordinal",
            (result_id, offset),
        )
        for (entry,) in rows:
            if len(json.dumps(page | entry).encode()) > data["max_response_bytes"]:
                if not count:
                    raise CatalogError("response_budget_too_small")
                break
            page.update(entry)
            count += 1
    if offset + count < data["count"]:
        conn.execute(
            "INSERT INTO query_cursors VALUES (%s,%s,%s)", (continuation, result_id, offset + count)
        )
    else:
        page["_continuation"]["next_cursor"] = None
    return page
