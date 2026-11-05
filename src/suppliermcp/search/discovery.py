import hashlib
import json
from suppliermcp.catalog.contracts import CatalogError,CatalogQuery,SearchResult
from suppliermcp.catalog.repository import get_product,read_status
from .index import ALIAS,normalize
from .listing import matching_ids,materialize


def search(conn,client,text,filters,principal):
    if not text.strip() or len(text)>1000:
        raise CatalogError('invalid_search_text')
    candidates=[]
    found=0
    for page in range(1,5):
        data=client.request('GET',f'/collections/{ALIAS}/documents/search',params={
            'q':normalize(text),'query_by':'text','per_page':250,'page':page,
            'drop_tokens_threshold':0,'num_typos':0,'prefix':'false'}).json()
        found=data['found']
        candidates.extend(hit['document']['id'] for hit in data['hits'])
        if len(candidates)>=found:
            break
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        confirmed,unknown=matching_ids(conn,CatalogQuery(filters=filters))
        allowed=set(confirmed)
        ids=list(dict.fromkeys(i for i in candidates if i in allowed))
        products=[get_product(conn,i) for i in ids]
        coverage=read_status(conn)
        coverage.complete=False
        coverage.warnings.append('text_discovery_is_not_exhaustive')
        if coverage.index_revision<coverage.revision:
            coverage.warnings.append('index_lag')
        if found>1000:
            coverage.warnings.append('candidate_scan_limited_to_1000')
        digest=hashlib.sha256(json.dumps({'text':text,'filters':[f.model_dump() for f in filters]},sort_keys=True).encode()).hexdigest()
        result=materialize(conn,products,coverage,principal,digest,unknown_total=len(set(unknown)&set(candidates)))
        return SearchResult(**result.model_dump())
