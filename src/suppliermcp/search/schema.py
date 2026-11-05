import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.catalog.repository import get_product

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
            "SELECT 1 FROM source_schema WHERE kind='ProductCategory' AND 'ed:' || (data->>'CategoryCode')=%s LIMIT 1",
            (category,),
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
    for item_id in item_ids:
        conn.execute("DELETE FROM catalog_values WHERE item_id=%s", (item_id,))
        try:
            view = get_product(conn, item_id)
        except CatalogError:
            continue
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
        for o in view.item.observations:
            if o.derivation == "mapped":
                continue
            field = f"native:{o.interface}:{o.field}"
            native.setdefault(field, set())
            if o.state == "known" and isinstance(o.value, (str, int, float)):
                native[field].add(str(o.value))
        for field, entries in native.items():
            values[field] = (next(iter(entries)) if len(entries) == 1 else None, "text")
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
            state = "known" if value is not None and value != "unknown" else "unknown"
            conn.execute(
                "INSERT INTO catalog_values VALUES (%s,%s,%s,%s,%s)",
                (item_id, field, str(value) if value is not None else None, state, kind),
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
