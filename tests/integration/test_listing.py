from decimal import Decimal
import pytest
from suppliermcp.catalog.contracts import BatchManifest, SourceItem, Observation, Offer, CatalogQuery, Filter, Identifier, CatalogError
from suppliermcp.sync.publish import stage,publish
from suppliermcp.search.listing import start_listing,next_page
from suppliermcp.search.exact import lookup


def seed(conn):
    rows=[]
    for i in range(25):
        rows.append(SourceItem(supplier='mega',source_id=str(i),sku=f'{i:03}',name=f'Memory {i}',manufacturer='Acme'))
    publish(conn,stage(conn,BatchManifest(interface='mega',domain='catalog',complete=True,artifact_sha256='listing'),rows))


def test_exact_and_stable_pagination(conn):
    seed(conn)
    assert lookup(conn,[Identifier(kind='sku',supplier='mega',value='001')]).entries[0]['status']=='found'
    assert lookup(conn,[Identifier(kind='sku',supplier='mega',value='1')]).entries[0]['status']=='missing'
    first=start_listing(conn,CatalogQuery(), 'alice')
    assert first.total==25 and len(first.results)==20
    conn.execute("UPDATE source_items SET data=jsonb_set(data,'{name}','\"Changed\"')")
    second=next_page(conn,first.next_cursor,'alice')
    assert len(second.results)==5 and all(p.item.name!='Changed' for p in second.results)
    assert len({p.product_id for p in first.results+second.results})==25
    with pytest.raises(CatalogError,match='result_not_found'): next_page(conn,first.next_cursor,'bob')
    conn.execute("UPDATE query_results SET expires_at=now()-interval '1 second'")
    with pytest.raises(CatalogError,match='result_expired'): next_page(conn,first.next_cursor,'alice')


def test_three_valued_filter(conn):
    seed(conn)
    query=CatalogQuery(filters=[Filter(field='price',operator='lte',value=100)])
    page=start_listing(conn,query,'alice')
    assert page.total==0 and page.unknown_total==25
    assert start_listing(conn,query.model_copy(update={'classification':'unknown'}),'alice').total==25


def test_invalid_field_not_ignored(conn):
    seed(conn)
    with pytest.raises(CatalogError,match='unsupported_filter'):
        start_listing(conn,CatalogQuery(filters=[Filter(field='anything; DROP TABLE source_items',operator='eq',value=1)]),'alice')


def test_scope_and_currency_are_validated(conn):
    from suppliermcp.search.schema import catalog_schema
    seed(conn)
    with pytest.raises(CatalogError) as error:
        catalog_schema(conn, 'invented')
    assert error.value.code=='unknown_category'
    with pytest.raises(CatalogError, match='unsupported_currency'):
        start_listing(conn, CatalogQuery(sort='price_asc', currency='XYZ'), 'alice')


def test_partition_boundaries_are_queryable(conn):
    seed(conn)
    query=CatalogQuery(source_id_from='mega:1', source_id_to='mega:20')
    page=start_listing(conn,query,'alice')
    assert [p.product_id for p in page.results]==['mega:1','mega:10','mega:11','mega:12','mega:13','mega:14','mega:15','mega:16','mega:17','mega:18','mega:19','mega:2']


def test_cursor_rejects_changed_query(conn):
    seed(conn)
    page=start_listing(conn,CatalogQuery(),'alice')
    with pytest.raises(CatalogError,match='result_query_mismatch'):
        next_page(conn,page.next_cursor,'alice',query_hash='changed')


def test_large_result_returns_exact_partitions(conn):
    conn.execute("INSERT INTO source_items(id,data,active,revision) SELECT 'mega:'||lpad(i::text,6,'0'), '{}'::jsonb,true,1 FROM generate_series(1,100001) i")
    with pytest.raises(CatalogError) as error:
        start_listing(conn,CatalogQuery(),'alice')
    import json
    assert error.value.code=='result_too_large'
    details=json.loads(error.value.message)
    assert details=={'count':100001,'partitions':[{'source_id_from':'mega:000001','source_id_to':'mega:100001'},{'source_id_from':'mega:100001','source_id_to':None}]}


def test_page_payload_budget(conn):
    seed(conn)
    conn.execute("UPDATE source_items SET data=jsonb_set(data,'{name}',to_jsonb(repeat('x',150000)))")
    page=start_listing(conn,CatalogQuery(),'alice')
    assert len(page.results)==1 and page.next_cursor
    conn.execute("UPDATE source_items SET data=jsonb_set(data,'{name}',to_jsonb(repeat('x',260000)))")
    with pytest.raises(CatalogError) as error:
        start_listing(conn,CatalogQuery(),'alice')
    assert error.value.code=='item_too_large'
