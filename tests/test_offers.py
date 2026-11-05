from decimal import Decimal
from datetime import timedelta
import pytest
from suppliermcp.catalog.contracts import Offer, utcnow
from suppliermcp.catalog.offers import quote, compare


def test_exact_decimal_and_explicit_rounding():
    now=utcnow()
    offer=Offer(item_id='mega:1',unit_net='0.10',fees_net='0',currency='CZK',order_multiple='1')
    assert quote(offer,Decimal('3'),now).total_net==Decimal('0.30')
    result=quote(offer.model_copy(update={'order_multiple':Decimal('5')}),Decimal('3'),now)
    assert result.requested_qty==3 and result.orderable_qty==5
    assert result.total_net==Decimal('0.50')


def test_unknown_fee_rule_and_currency():
    now=utcnow()
    offer=Offer(item_id='ed:1',unit_net='10',currency='CZK')
    assert quote(offer,Decimal('1'),now).total_net is None
    offer=offer.model_copy(update={'fees_net':Decimal('0'),'price_rule':'valuepack','discount_min_qty':Decimal('5'),'order_multiple':Decimal('1')})
    assert quote(offer,Decimal('1'),now).total_net is None
    assert quote(offer,Decimal('5'),now).total_net==Decimal('50')
    with pytest.raises(ValueError): quote(offer,Decimal('NaN'),now)


def test_stale_and_incomparable_winners():
    now=utcnow()
    a=Offer(item_id='ed:1',unit_net='5',fees_net='0',currency='CZK',order_multiple='1',
            source_updated_at=now-timedelta(days=1),freshness_seconds=3600)
    b=Offer(item_id='mega:1',unit_net='6',fees_net='0',currency='CZK',order_multiple='1',source_updated_at=now,freshness_seconds=3600)
    result=compare([a,b],Decimal('1'),now)
    assert result.last_known_winner=='ed:1' and result.fresh_winner=='mega:1'
    assert compare([a,b.model_copy(update={'currency':'EUR'})],Decimal('1'),now).last_known_winner is None
    assert compare([a],Decimal('1'),now).fresh_winner is None
    assert not quote(b.model_copy(update={'source_updated_at':None}),Decimal('1'),now).fresh
