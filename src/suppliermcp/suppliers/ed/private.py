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
        codes = sorted({e.text for e in root.iter() if local(e.tag) == "CommodityCode" and e.text})
        manifests, failures = [], []
        for code in codes:
            try:
                data = self.gateway.call(
                    "getProductCatalogueFullDownloadXML", onStock=False, Comodities=code
                )
                response = fromstring(data, forbid_dtd=True)
                values = {local(e.tag): e.text for e in response.iter() if not len(e)}
                if values.get("StatusCode") == "ERROR" or values.get("IsReady", "true").lower() in {
                    "false",
                    "0",
                }:
                    raise CatalogError("export_not_ready")
                if values.get("Url"):
                    data = self.transport.read("GET", values["Url"], endpoint="download")
                manifest = BatchManifest(
                    interface=self.interface,
                    domain="catalog",
                    mode="targeted",
                    endpoint="getProductCatalogueFullDownloadXML",
                )
                self.store.save([data], manifest)
                manifests.append(manifest)
            except CatalogError:
                failures.append(code)
        return manifests, failures
