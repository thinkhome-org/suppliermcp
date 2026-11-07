from defusedxml.ElementTree import fromstring

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, utcnow

from .public import EdPublicAdapter, local


class EdPrivateAdapter(EdPublicAdapter):
    interface = "ed_private"
    methods = {
        "catalog": "getProductCatalogueDownloadXML",
        "price": "getProductCatalogueStockDownloadXML",
        "stock": "getProductCatalogueStockDownloadXML",
        "schema": "getNavigator",
    }

    def commodity_codes(self):
        if not self.gateway or not self.store:
            raise CatalogError("source_not_configured")
        root = fromstring(self.gateway.call("getProductCommodityList"), forbid_dtd=True)
        return sorted(
            {
                e.text.strip()
                for e in root.iter()
                if local(e.tag) == "CommodityCode" and e.text and e.text.strip()
            }
        )

    def fetch_commodity(self, code):
        manifest = BatchManifest(
            interface=self.interface,
            domain="catalog",
            mode="targeted",
            endpoint="getProductCatalogueFullDownloadXML",
            started_at=utcnow(),
        )
        return self._fetch_manifest(
            manifest, {"onStock": False, "Comodities": code}, require_url=True
        )

    def dictionaries(self):
        manifests, failures = [], []
        for endpoint in [
            "getNavigator",
            "getProductProducerList",
            "getProductCommodityList",
            "getProductRelationList",
        ]:
            started_at = utcnow()
            try:
                data = self.gateway.call(endpoint)
                root = fromstring(data, forbid_dtd=True)
                if any(
                    local(e.tag) == "Fault" or local(e.tag) == "StatusCode" and e.text == "ERROR"
                    for e in root.iter()
                ):
                    raise CatalogError("supplier_response_error")
                manifest = BatchManifest(
                    interface=self.interface,
                    domain="schema",
                    mode="targeted",
                    endpoint=endpoint,
                    started_at=started_at,
                )
                self.store.save([data], manifest)
                manifests.append(manifest)
            except Exception:
                failures.append(endpoint)
        return manifests, failures
