"""Scalar SOAP reads verified against the public eD WSDL (2026-11-05)."""

from xml.etree.ElementTree import Element, SubElement, tostring

from suppliermcp.catalog.contracts import CatalogError

READS = {
    "getProductListDownloadXML",
    "getProductListDownloadZIP",
    "getProductCatalogueDownloadXML",
    "getProductDetail",
    "getProductCatalogueStockDownloadXML",
    "getNavigator",
    "getProductCommodityList",
    "getProductCatalogueFullDownloadXML",
    "getProductRelationList",
    "getProductProducerList",
}


class EdGateway:
    def __init__(self, transport, url, login, password):
        self.transport, self.url, self.login, self.password = transport, url, login, password

    def call(self, method, **params):
        if method not in READS:
            raise CatalogError("operation_not_allowed")
        envelope = Element(
            "soap:Envelope", {"xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/"}
        )
        body = SubElement(envelope, "soap:Body")
        operation = SubElement(body, method, {"xmlns": "http://www.elinkx.cz"})
        for name, value in {"login": self.login, "password": self.password, **params}.items():
            SubElement(operation, name).text = (
                str(value).lower() if isinstance(value, bool) else str(value)
            )
        return self.transport.read(
            "POST",
            self.url,
            endpoint=method,
            body=tostring(envelope),
            soap_action=f'"http://www.elinkx.cz/{method}"',
        )
