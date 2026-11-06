"""Exact catalog XML paths from reviewed eD WSDLs, eD manuals and 100MEGA XDRs."""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from xml.etree.ElementTree import Element

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.suppliers.registry import resolve_operation

ED = "http://www.elinkx.cz"
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"


@cache
def _schemas():
    return json.loads(files(__package__).joinpath("catalog_projection.json").read_text())


def _name(tag):
    namespace, _, local = tag.rpartition("}")
    return namespace.removeprefix("{"), local


@dataclass(frozen=True)
class Projection:
    types: dict
    kind: str
    namespace: str

    @property
    def text(self):
        return self.kind == "$"

    def allows_attribute(self, name):
        return not self.text and name in self.types[self.kind][1]

    def child(self, tag):
        ns, name = _name(tag)
        if self.text:
            return None
        child_type = self.types[self.kind][0].get(name)
        child_ns = SOAP if self.kind == "!Envelope" else self.namespace
        if not child_type or ns not in {"", child_ns}:
            return None
        return Projection(self.types, child_type, self.namespace)

    def project(self, element):
        selected = Element(
            element.tag,
            {name: value for name, value in element.attrib.items() if self.allows_attribute(name)},
        )
        if self.text:
            if not len(element):
                selected.text = element.text
            return selected
        for child in element:
            projection = self.child(child.tag)
            if projection:
                selected.append(projection.project(child))
        return selected


def catalog_projection(interface, endpoint, root_name, *, soap_result=False):
    """Select a reviewed root. Unknown roots have no publishable catalog fields."""
    ns, root = _name(root_name)
    if interface == "mega":
        types = _schemas().get("mega." + endpoint)
        if (
            not types
            or root != ("SHOP" if endpoint in {"StoItemShop_El", "StoItemShoptet_El"} else "Result")
            or ns
        ):
            raise CatalogError("catalog_projection_unavailable")
        return Projection(types, root, "")
    spec = resolve_operation(f"{interface}.{endpoint}")
    if spec.scope != "catalog:read" or interface not in {"ed_public", "ed_private"}:
        raise CatalogError("catalog_projection_unavailable")
    types = _schemas()[interface]
    if root == "Envelope" and ns in ("", SOAP):
        wrappers = {
            "!Envelope": [{"Body": "!Body"}, []],
            "!Body": [{endpoint + "Response": "!Response"}, []],
            "!Response": [{endpoint + "Result": spec.output_schema}, []],
        }
        return Projection(types | wrappers, "!Envelope", ED)
    if ns not in {"", ED}:
        raise CatalogError("catalog_projection_unavailable")
    if soap_result and root == endpoint + "Result":
        return Projection(types, spec.output_schema, ED)
    if spec.strategy != "download":
        # Some worker fixtures and import artifacts contain the unwrapped result array.
        if root == spec.output_schema or root == endpoint + "Result":
            kind = spec.output_schema
        elif root in types[spec.output_schema][0]:
            kind = types[spec.output_schema][0][root]
        elif endpoint == "getNavigator" and root == "Navigator":
            return Projection(
                types | {"!Navigator": [{"ProductCategory": "ProductCategory"}, []]},
                "!Navigator",
                ED,
            )
        elif endpoint == "getProductDetail" and root in {"Product", "ProductComplete"}:
            kind = "ProductComplete"
        elif endpoint == "getProductList" and root in {"ArrayOfProduct", "ProductList"}:
            kind = "ArrayOfProduct"
        else:
            raise CatalogError("catalog_projection_unavailable")
    elif interface == "ed_public":
        allowed = (
            {"PRICELIST"}
            if "WithTransform" in endpoint
            else {"ResponseProductList", "ArrayOfProduct"}
        )
        if root not in allowed:
            raise CatalogError("catalog_projection_unavailable")
        kind = root
    else:
        if "ShortDownload" in endpoint:
            kind = "ArrayOfProductSimple"
        elif "StockDownload" in endpoint:
            kind = "ArrayOfProductShort"
        elif "Full" in endpoint:
            kind = "ArrayOfProductComplete"
        else:
            kind = "ArrayOfProduct"
        if kind != root:
            raise CatalogError("catalog_projection_unavailable")
    return Projection(types, kind, ED)
