from decimal import Decimal, InvalidOperation

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.catalog.repository import get_product

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
    if category is not None:
        raise CatalogError(
            "unknown_category", "No verified category mapping is installed for this category"
        )
    types = dict(BASE)
    types.update(dict(conn.execute("SELECT DISTINCT field,value_type FROM catalog_values")))
    return {
        field: {
            "type": kind,
            "operators": ["eq", "in", "gte", "lte"] if kind == "number" else ["eq", "in"],
        }
        for field, kind in sorted(types.items())
    }


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
            field = f"native:{o.interface}:{o.field}"
            native.setdefault(field, set())
            if o.state == "known" and isinstance(o.value, (str, int, float)):
                native[field].add(str(o.value))
        for field, entries in native.items():
            values[field] = (next(iter(entries)) if len(entries) == 1 else None, "text")
        for field, (value, kind) in values.items():
            state = "known" if value is not None and value != "unknown" else "unknown"
            conn.execute(
                "INSERT INTO catalog_values VALUES (%s,%s,%s,%s,%s)",
                (item_id, field, str(value) if value is not None else None, state, kind),
            )
