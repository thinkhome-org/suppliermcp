from decimal import Decimal

from suppliermcp.catalog.contracts import Offer, utcnow
from suppliermcp.catalog.offers import compare
from suppliermcp.suppliers.ed.gateway import READS


def test_read_only_and_uncertain_price_workflow():
    assert not any(
        word in name.lower()
        for name in READS
        for word in ["order", "invoice", "claim", "create", "update", "delete"]
    )
    offer = Offer(item_id="mega:1", unit_net="1", currency="CZK")
    result = compare([offer], Decimal(7), utcnow())
    assert result.offers[0].unit_net == 1 and result.offers[0].total_net is None
    assert result.fresh_winner is None and result.last_known_winner is None
