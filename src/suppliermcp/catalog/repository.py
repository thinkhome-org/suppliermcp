from suppliermcp.catalog.contracts import CatalogError, Coverage, Offer, ProductView, SourceItem


def read_status(conn, enabled_interfaces=None):
    rev = conn.execute("SELECT COALESCE(max(revision),0) FROM domain_checkpoints").fetchone()[0]
    pending = conn.execute("SELECT min(revision) FROM index_outbox WHERE NOT done").fetchone()[0]
    states = dict(conn.execute("SELECT interface,data FROM source_state").fetchall())
    configured = (
        set(enabled_interfaces)
        if enabled_interfaces is not None
        else {k for k, v in states.items() if v.get("configured")}
    )
    for interface in ["ed_public", "ed_private", "mega"]:
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
    row = conn.execute(
        "SELECT data FROM source_items WHERE id=%s AND active", (product_id,)
    ).fetchone()
    if not row:
        raise CatalogError("product_not_found")
    item = SourceItem.model_validate(row[0])
    obs = conn.execute("SELECT data FROM observations WHERE item_id=%s", (product_id,)).fetchall()
    if obs:
        from .contracts import Observation

        item.observations = [Observation.model_validate(r[0]) for r in obs]
    from suppliermcp.search.schema import mapped_observations

    item.observations.extend(mapped_observations(item.observations))
    rows = conn.execute(
        "SELECT data FROM current_offers WHERE item_id=%s", (product_id,)
    ).fetchall()
    offers = [Offer.model_validate(r[0]) for r in rows]
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
    relationships = [
        r[0] for r in conn.execute("SELECT data FROM relationships WHERE item_id=%s", (product_id,))
    ]
    return ProductView(
        product_id=product_id,
        item=item,
        offers=[combined] if combined else [],
        conflicts=conflicts,
        relationships=relationships,
    )
