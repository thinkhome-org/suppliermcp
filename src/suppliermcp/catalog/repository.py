from suppliermcp.catalog.contracts import CatalogError, Coverage, Offer, ProductView, SourceItem
from suppliermcp.suppliers.profiles import CATALOG_INTERFACES


def read_status(conn, enabled_interfaces=None):
    rev = conn.execute("SELECT COALESCE(max(revision),0) FROM domain_checkpoints").fetchone()[0]
    pending = conn.execute("SELECT min(revision) FROM index_outbox WHERE NOT done").fetchone()[0]
    states = {
        name: state
        for name, state in conn.execute("SELECT interface,data FROM source_state").fetchall()
        if name in CATALOG_INTERFACES
    }
    configured = (
        set(enabled_interfaces).intersection(CATALOG_INTERFACES)
        if enabled_interfaces is not None
        else {k for k, v in states.items() if v.get("configured")}
    )
    for interface in CATALOG_INTERFACES:
        state = states.setdefault(interface, {"outcome": "not_fetched", "domains": {}})
        state["configured"] = interface in configured
        if interface not in configured:
            state["outcome"] = "disabled"
    complete = bool(configured) and all(
        states[k].get("outcome") == "ok"
        and states[k].get("domains", {}).get("catalog", {}).get("complete")
        and states[k].get("domains", {}).get("catalog", {}).get("last_verified_complete_revision")
        is not None
        for k in configured
    )
    return Coverage(
        interfaces=states,
        revision=rev,
        index_revision=rev if pending is None else max(0, pending - 1),
        complete=complete,
        warnings=["coverage_is_account_and_field_scoped"],
    )


def get_product(conn, product_id):
    products = get_products(conn, [product_id])
    if not products:
        raise CatalogError("product_not_found")
    return products[0]


def get_products(conn, product_ids, *, include_evidence=True):
    from collections import defaultdict

    items = dict(
        conn.execute(
            "SELECT id,data FROM source_items WHERE id=ANY(%s) AND active", (list(product_ids),)
        )
    )
    observations, offers, relationships = defaultdict(list), defaultdict(list), defaultdict(list)
    if include_evidence:
        for item_id, data in conn.execute(
            "SELECT item_id,data FROM observations WHERE item_id=ANY(%s)", (list(items),)
        ):
            observations[item_id].append((data,))
        for item_id, data in conn.execute(
            "SELECT item_id,data FROM relationships WHERE item_id=ANY(%s)", (list(items),)
        ):
            relationships[item_id].append(data)
    for item_id, data, interface, endpoint in conn.execute(
        "SELECT item_id,data,interface,endpoint FROM current_offers WHERE item_id=ANY(%s)",
        (list(items),),
    ):
        offers[item_id].append((data, interface, endpoint))
    result = [
        _assemble(
            item_id, items[item_id], observations[item_id], offers[item_id], relationships[item_id]
        )
        for item_id in product_ids
        if item_id in items
    ]
    if not include_evidence:
        for view in result:
            view.item.observations = []
            for offer in view.offers:
                offer.observations = []
            view.detail_continuation = {
                "product_id": view.product_id,
                "tool": "get_product",
                "sections": ["overview", "observations", "attachments", "relationships"],
            }
    return result


def _assemble(product_id, data, obs, rows, relationships):
    item = SourceItem.model_validate(data)
    if obs:
        from .contracts import Observation

        item.observations = [Observation.model_validate(r[0]) for r in obs]
    from suppliermcp.search.schema import mapped_observations

    item.observations.extend(mapped_observations(item.observations))
    offers = []
    for data, interface, endpoint in rows:
        offer = Offer.model_validate(data)
        offer.observations = [
            o for o in item.observations if o.interface == interface and o.endpoint == endpoint
        ] or offer.observations
        offers.append(offer)
    # Keep source/interface-specific evidence; never select a conflicting price silently.
    conflicts = []
    combined = None
    if offers:
        priced = [o for o in offers if o.unit_net is not None]
        combined = max(priced or offers, key=lambda o: o.evidence_at).model_copy(deep=True)
        for field in [
            "currency",
            "unit_net",
            "fees_net",
            "vat_percent",
            "order_multiple",
            "discount_min_qty",
            "discount",
        ]:
            present = [o for o in offers if getattr(o, field) is not None]
            if not present:
                setattr(combined, field, None)
            elif len({str(getattr(o, field)) for o in present}) == 1:
                setattr(combined, field, getattr(present[0], field))
            elif all(o.source_updated_at for o in present):
                latest = max(present, key=lambda o: o.source_updated_at)
                winners = [o for o in present if o.source_updated_at == latest.source_updated_at]
                if len({str(getattr(o, field)) for o in winners}) == 1:
                    setattr(combined, field, getattr(latest, field))
                else:
                    setattr(combined, field, None)
                    conflicts.append(field)
            else:
                setattr(combined, field, None)
                conflicts.append(field)
        known_stock = [o for o in offers if o.stock_state != "unknown"]
        if known_stock:
            latest = max(known_stock, key=lambda o: o.stock_evidence_at or o.evidence_at)
            combined.stock_state, combined.stock_qty = latest.stock_state, latest.stock_qty
            combined.stock_evidence_at = latest.stock_evidence_at or latest.evidence_at
        price_evidence = [o for o in offers if o.unit_net is not None]
        if price_evidence:
            combined.evidence_at = min(o.evidence_at for o in price_evidence)
            combined.source_updated_at = (
                None
                if any(o.source_updated_at is None for o in price_evidence)
                else min((o.source_updated_at for o in price_evidence), default=None)
            )
            combined.refresh_failed = any(o.refresh_failed for o in price_evidence)
            combined.freshness_seconds = (
                min(o.freshness_seconds for o in price_evidence)
                if all(o.freshness_seconds is not None for o in price_evidence)
                else None
            )
        price_rules = {o.price_rule for o in offers if o.unit_net is not None}
        if len(price_rules) == 1:
            combined.price_rule = next(iter(price_rules))
        if len(price_rules) > 1:
            combined.price_rule = "unknown"
            conflicts.append("price_rule")
        combined.observations = [v for o in offers for v in o.observations]
    return ProductView(
        product_id=product_id,
        item=item,
        offers=[combined] if combined else [],
        conflicts=conflicts,
        relationships=relationships,
    )
