from suppliermcp.catalog.contracts import utcnow

from .public import EdPublicAdapter


class EdPrivateAdapter(EdPublicAdapter):
    interface = "ed_private"
    methods = {
        "catalog": "getProductCatalogueDownloadXML",
        "price": "getProductCatalogueStockDownloadXML",
        "stock": "getProductCatalogueStockDownloadXML",
        "schema": "getNavigator",
    }

    def enrichment(self):
        """Retain successful chunks while reporting missing commodity coverage."""
        from defusedxml.ElementTree import fromstring

        from suppliermcp.catalog.contracts import BatchManifest, CatalogError

        from .public import local

        if not self.gateway or not self.store:
            raise CatalogError("source_not_configured")
        root = fromstring(self.gateway.call("getProductCommodityList"), forbid_dtd=True)
        codes = sorted(
            {
                e.text.strip()
                for e in root.iter()
                if local(e.tag) == "CommodityCode" and e.text and e.text.strip()
            }
        )
        failures = [] if codes else ["commodity_list_empty"]

        def chunks():
            for code in codes:
                manifest = BatchManifest(
                    interface=self.interface,
                    domain="catalog",
                    mode="targeted",
                    endpoint="getProductCatalogueFullDownloadXML",
                    started_at=utcnow(),
                )
                try:
                    yield self._fetch_manifest(
                        manifest, {"onStock": False, "Comodities": code}, require_url=True
                    )
                except CatalogError:
                    failures.append(code)

        return chunks(), failures

    def dictionaries(self):
        from defusedxml.ElementTree import fromstring

        from suppliermcp.catalog.contracts import BatchManifest, CatalogError

        from .public import local

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
