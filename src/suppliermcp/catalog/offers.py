from decimal import ROUND_CEILING

from suppliermcp.catalog.contracts import Comparison, OfferQuote, QuantityRequest


def quote_components(offer, quantity, now):
    quantity = QuantityRequest(quantity=quantity).quantity
    multiple = offer.order_multiple
    orderable = (
        (quantity / multiple).to_integral_value(rounding=ROUND_CEILING) * multiple
        if multiple
        else None
    )
    reasons = []
    if multiple is None:
        reasons.append("order_multiple_unknown")
    if offer.unit_net is None:
        reasons.append("price_unknown")
    if offer.fees_net is None:
        reasons.append("fees_unknown")
    if offer.currency is None:
        reasons.append("currency_unknown")
    unit = offer.unit_net
    if offer.price_rule == "unknown":
        reasons.append("price_rule_unknown")
    elif offer.price_rule == "valuepack":
        if not offer.discount_min_qty or orderable is None:
            reasons.append("discount_eligibility_unknown")
        elif orderable < offer.discount_min_qty:
            if offer.discount is None:
                reasons.append("undiscounted_price_unknown")
            elif unit is not None:
                unit += offer.discount
    fresh = bool(
        offer.source_updated_at
        and offer.freshness_seconds
        and not offer.refresh_failed
        and 0 <= (now - offer.source_updated_at).total_seconds() <= offer.freshness_seconds
    )
    return OfferQuote(
        item_id=offer.item_id,
        requested_qty=quantity,
        orderable_qty=orderable,
        unit_net=unit,
        fees_net=offer.fees_net,
        currency=offer.currency,
        fresh=fresh,
        evidence_at=offer.evidence_at,
        reasons=reasons,
    )


def quote(offer, quantity, now):
    result = quote_components(offer, quantity, now)
    if not result.reasons:
        result.total_net = (result.unit_net + result.fees_net) * result.orderable_qty
    return result


def compare(offers, quantity, now):
    quotes = [quote(o, quantity, now) for o in offers]
    comparable = [q for q in quotes if q.total_net is not None]
    warnings = []
    if len({q.currency for q in comparable}) > 1:
        warnings.append("multiple_currencies_not_ranked")
        comparable = []
    # All totals are net-of-VAT, including known fees; never compare differing quantities.
    if len({q.orderable_qty for q in comparable}) > 1:
        warnings.append("different_orderable_quantities_not_ranked")
        comparable = []
    fresh = [q for q in comparable if q.fresh]
    return Comparison(
        offers=quotes,
        incomparable_ids=[q.item_id for q in quotes if not comparable or q.total_net is None],
        last_known_winner=min(comparable, key=lambda q: q.total_net).item_id
        if comparable
        else None,
        fresh_winner=min(fresh, key=lambda q: q.total_net).item_id if fresh else None,
        warnings=warnings,
    )
