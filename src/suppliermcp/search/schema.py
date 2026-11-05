import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.catalog.repository import get_products

MAPPINGS = json.loads((Path(__file__).parents[1] / "catalog/mappings.json").read_text())

BASE = {
    "supplier": "text",
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
        batch = ids[start : start + 200]
        views = get_products(conn, batch)
        conn.execute("DELETE FROM catalog_values WHERE item_id=ANY(%s)", (batch,))
        with conn.cursor().copy(
            "COPY catalog_values (item_id,field,value,state,value_type,value_key) FROM STDIN"
        ) as copy:
            for view in views:
                for row in _value_rows(view):
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
    conflicted = set()
    for o in view.item.observations:
        if o.derivation == "mapped":
            continue
        field = f"native:{o.interface}:{o.field}"
        native.setdefault(field, set())
        native_types.setdefault(field, set()).add(o.value_type)
        if o.cardinality == "many":
            many.add(field)
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
    for field, entries in native.items():
        if len(native_types[field]) != 1:
            conflicted.add(field)
        values[field] = (
            next(iter(entries)) if len(entries) == 1 and field not in conflicted else None,
            "number" if native_types[field] == {"number"} else "text",
        )
    mapped = {}
    for native, mapping in MAPPINGS.items():
        value = values.get(native, (None, "text"))[0]
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
