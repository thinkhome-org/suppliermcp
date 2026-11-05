from decimal import Decimal
from suppliermcp.catalog.contracts import Offer, BatchManifest, SourceItem, utcnow
from suppliermcp.sync.publish import stage,publish
from suppliermcp.catalog.repository import get_product
from suppliermcp.catalog.offers import quote


def test_missing_price_in_new_export_keeps_old_evidence(conn):
    t=utcnow()
    item=SourceItem(supplier='mega',source_id='1',sku='1',name='One')
    m=BatchManifest(interface='mega',domain='catalog',complete=True,artifact_sha256='a')
    publish(conn,stage(conn,m,[item,Offer(item_id='mega:1',unit_net='10',fees_net='0',currency='CZK',evidence_at=t)]))
    m2=m.model_copy(update={'artifact_sha256':'b','started_at':utcnow()})
    publish(conn,stage(conn,m2,[item,Offer(item_id='mega:1')]))
    offer=get_product(conn,'mega:1').offers[0]
    assert offer.unit_net==Decimal('10') and offer.evidence_at==t
