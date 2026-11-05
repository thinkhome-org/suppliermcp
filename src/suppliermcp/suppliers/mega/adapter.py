from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

from suppliermcp.catalog.contracts import BatchManifest, Capabilities, CatalogError, Observation, Offer, SourceItem
from suppliermcp.sync.artifacts import parse_xml
from .capabilities import require_window


class MegaAdapter:
    interface = 'mega'
    endpoints = {'catalog':'StoItemBase','stock':'StoItemQtyFree','price':'StoItemPriceOrd'}

    def __init__(self, transport=None, store=None, contracts=None, base_url='https://i6ws.100mega.cz'):
        self.transport, self.store = transport, store
        self.contracts, self.base_url = contracts or {}, base_url

    def discover(self):
        return Capabilities(domains=[d for d,e in self.endpoints.items() if e in self.contracts],
                            endpoints={e:c.get('modes',[]) for e,c in self.contracts.items()},
                            windows={e:{k:c.get(k) for k in ['timezone','days','hours']} for e,c in self.contracts.items()},
                            coverage='partial' if self.contracts else 'unknown')

    def fetch(self, domain, codes=None):
        endpoint = self.endpoints.get(domain)
        if not endpoint:
            raise CatalogError('unsupported_domain')
        mode = 'targeted' if codes else 'full'
        require_window(self.contracts.get(endpoint, {}), mode)
        if codes and len(codes) != 1:
            raise CatalogError('unsupported_targeted_read')
        params = {'resultType':endpoint}
        if codes:
            params['code'] = codes[0]
        method = 'GetResultByCode' if codes else 'GetResult'
        data = self.transport.read('GET', f'{self.base_url}/Default.asmx/{method}?{urlencode(params)}', endpoint=method)
        manifest = BatchManifest(interface='mega',domain=domain,mode=mode,endpoint=endpoint,capabilities=self.discover())
        self.store.save([data],manifest)
        return manifest

    def parse(self, manifest):
        contract = self.contracts.get(manifest.endpoint,{})
        root_seen = False
        for element in parse_xml(Path(manifest.path)):
            tag = element.tag.rsplit('}',1)[-1]
            if tag == 'Result':
                root_seen = True
            if tag != 'StoItem':
                continue
            values = dict(element.attrib)
            if not values.get('Id') or not values.get('Code'):
                raise CatalogError('missing_product_identity')
            if manifest.endpoint == 'StoItemBase':
                values.setdefault('QtyPack','1')
            observations = [Observation(interface='mega',endpoint=manifest.endpoint,field=k,value=v,
                fetched_at=manifest.started_at,source_updated_at=manifest.source_updated_at,
                artifact_sha256=manifest.artifact_sha256) for k,v in values.items()]
            def num(key):
                value = values.get(key)
                if value is None:
                    return None
                try:
                    result = Decimal(value)
                    if not result.is_finite() or result < 0:
                        raise ValueError()
                    return result
                except (InvalidOperation, ValueError):
                    raise CatalogError('invalid_numeric_field') from None
            yield SourceItem(supplier='mega',source_id=values['Id'],sku=values['Code'],name=values.get('Name',''),
                             manufacturer=values.get('ManName'),mpn=values.get('PartNo'),
                             ean=values.get(contract.get('ean_field','EAN_NOT_VERIFIED')),observations=observations)
            qty = num('QtyFree')
            state = 'unknown'
            if qty is not None:
                state = 'in_stock' if qty > 0 else 'out_of_stock'
            elif 'QtyFreeIs' in values:
                state = 'in_stock' if values['QtyFreeIs']=='1' else 'out_of_stock'
            elif contract.get('stock_mode') in {'flag','count'}:
                state = 'out_of_stock'
                if contract['stock_mode']=='count':
                    qty = Decimal('0')
            fees = None
            if 'PriceRef' in values and 'PriceRef2' in values:
                fees = num('PriceRef')+num('PriceRef2')
            yield Offer(item_id='mega:'+values['Id'],unit_net=num('PriceDea'),fees_net=fees,
                        currency=values.get(contract.get('currency_field','Currency'),contract.get('currency')),
                        vat_percent=num('TaxRate'),stock_qty=qty,stock_state=state,observations=observations,
                        fetched_at=manifest.started_at,evidence_at=manifest.started_at,
                        source_updated_at=manifest.source_updated_at)
            element.clear()
        if not root_seen:
            raise CatalogError('unexpected_export_root')
        manifest.complete = manifest.mode=='full' and contract.get('coverage')=='complete'
        manifest.stock_only = bool(contract.get('stock_only'))
