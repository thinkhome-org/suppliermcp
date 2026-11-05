from suppliermcp.catalog.contracts import LookupResult,CatalogError
from suppliermcp.catalog.repository import get_product,read_status


def lookup(conn,identifiers):
    if not 1<=len(identifiers)<=50:
        raise CatalogError('batch_limit')
    if not conn.execute('SELECT 1 FROM source_items LIMIT 1').fetchone():
        raise CatalogError('catalog_not_populated')
    entries=[]
    for identifier in identifiers:
        field={'sku':'sku','mpn':'mpn','ean':'ean'}[identifier.kind]
        query='SELECT id FROM source_items WHERE active AND data->>%s=%s'
        params=[field,identifier.value]
        if identifier.supplier:
            query+=" AND data->>'supplier'=%s";params.append(identifier.supplier)
        if identifier.kind=='mpn':
            query+=" AND lower(data->>'manufacturer')=lower(%s)";params.append(identifier.manufacturer)
        ids=[r[0] for r in conn.execute(query,params)]
        entries.append({'identifier':identifier.model_dump(),'status':'found' if len(ids)==1 else 'ambiguous' if ids else 'missing',
                        'products':[get_product(conn,i).model_dump(mode='json') for i in ids]})
    return LookupResult(entries=entries,coverage=read_status(conn))
