"""eD SOAP reads and export normalization; no ordering methods."""

import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree.ElementTree import tostring

from defusedxml.ElementTree import fromstring

from suppliermcp.catalog.contracts import (
    BatchManifest,
    Capabilities,
    CatalogError,
    Observation,
    Offer,
    SchemaRecord,
    SourceItem,
)
from suppliermcp.suppliers.offer_contract import apply_contract, import_projection
from suppliermcp.sync.artifacts import parse_xml

from .authority import BASELINE_METHODS, PLACEHOLDERS


def local(tag):
    return tag.rsplit("}", 1)[-1]


def fields(element):
    return {local(c.tag): c.text or "" for c in element if not len(c)}


class EdPublicAdapter:
    max_expanded_bytes = 1024**3
    max_description_bytes = 2 * 1024**2
    interface = "ed_public"
    methods = {
        "catalog": "getProductListDownloadZIP",
        "price": "getProductListDownloadZIP",
        "stock": "getProductListDownloadZIP",
    }

    def __init__(self, gateway=None, store=None, transport=None, sleep=time.sleep):
        self.gateway, self.store, self.transport, self.sleep = gateway, store, transport, sleep

    def discover(self):
        return Capabilities(
            domains=list(self.methods),
            endpoints={m: ["full"] for m in self.methods.values()},
            coverage="unknown",
        )

    def fetch(self, domain, codes=None):
        from suppliermcp.catalog.contracts import utcnow

        started_at = utcnow()
        if not self.gateway:
            raise CatalogError("source_not_configured")
        endpoint = (
            "getProductDetail"
            if codes and self.interface == "ed_private"
            else self.methods.get(domain)
        )
        if not endpoint:
            raise CatalogError("unsupported_domain")
        if codes and (len(codes) != 1 or self.interface == "ed_public"):
            raise CatalogError("unsupported_targeted_read")
        params = (
            {"code": codes[0]}
            if codes
            else ({"onStock": False, "encoding": "utf-8"} if self.interface == "ed_public" else {})
        )
        for _ in range(12):
            data = self.gateway.call(endpoint, **params)
            try:
                root = fromstring(data, forbid_dtd=True)
            except Exception:
                raise CatalogError("invalid_export") from None
            values = {local(e.tag): e.text for e in root.iter() if not len(e)}
            if values.get("StatusCode") == "ERROR" or any(
                local(e.tag) == "Fault" for e in root.iter()
            ):
                raise CatalogError("supplier_response_error")
            if (values.get("isReady", values.get("IsReady")) or "").lower() in {"false", "0"}:
                self.sleep(10)
                continue
            manifest = BatchManifest(
                interface=self.interface,
                requested_skus=codes or [],
                started_at=started_at,
                domain=domain,
                endpoint=endpoint,
                mode="targeted" if codes else "full",
                capabilities=self.discover(),
                authoritative_identity=self.interface == "ed_public"
                or endpoint in BASELINE_METHODS,
                replace_scope="items" if codes else "endpoint",
            )
            if not self.store:
                raise CatalogError("artifact_store_not_configured")
            url = values.get("url", values.get("Url"))
            if url:
                self.transport.download(url, self.store, manifest)
            else:
                self.store.save([data], manifest)
            return manifest
        raise CatalogError("export_not_ready", retryable=True)

    def parse(self, manifest):
        export_values = {}
        contract = getattr(self, "offer_contract", {})
        records = 0

        def check_status(element):
            name = local(element.tag)
            if name == "StatusCode" and element.text == "ERROR" or name == "Fault":
                raise CatalogError("supplier_response_error")

        for element in parse_xml(
            Path(manifest.path),
            max_expanded=self.max_expanded_bytes,
            projection=lambda name: import_projection(manifest, name, contract),
            validate_element=check_status,
        ):
            name = local(element.tag)
            if name == contract.get("export_timestamp_field"):
                export_values[name] = element.text
            if manifest.domain == "schema" and name in {
                "ProductRealationParent",
                "ProductRelationParent",
            }:
                parent = fields(element)
                for child in element.iter():
                    if local(child.tag) not in {"ProductRealationChild", "ProductRelationChild"}:
                        continue
                    values = fields(child)
                    if parent.get("ProId") and values.get("ProId"):
                        yield SchemaRecord(
                            interface=self.interface,
                            kind="relationship",
                            values={
                                "item_id": "ed:" + parent["ProId"],
                                "target_id": "ed:" + values["ProId"],
                                "kind": values.get("RelTypeId", "unknown"),
                                "name": values.get("RelTypeName"),
                                "quantity": values.get("Qty"),
                                "interface": self.interface,
                                "endpoint": manifest.endpoint,
                            },
                        )
            if manifest.domain == "schema" and name in {
                "ProductCategory",
                "ProductSuperCategory",
                "ProductCategoryAttribute",
                "ProductCategoryAttributeValue",
                "ProductCommodity",
                "ProductProducer",
                "ProductRelationParent",
            }:
                yield SchemaRecord(
                    interface=self.interface,
                    kind=name,
                    values={**fields(element), "_xml": tostring(element, encoding="unicode")},
                )
            if name not in {"Product", "ProductComplete", "ProductShort", "ProductSimple"}:
                continue
            values = fields(element)
            if not values.get("ProId") or not values.get("Code"):
                raise CatalogError("missing_product_identity")
            if any(len(str(v).encode()) > self.max_description_bytes for v in values.values()):
                raise CatalogError("description_too_large")
            observations = []
            for field, value in values.items():
                placeholder = manifest.endpoint in BASELINE_METHODS and field in PLACEHOLDERS
                state = "placeholder" if placeholder else ("known" if value else "missing")
                if field == "DateAvailible" and value.startswith(("1900-01-01", "1.1.1900")):
                    state = "missing"
                observations.append(
                    Observation(
                        interface=self.interface,
                        endpoint=manifest.endpoint,
                        field=field,
                        value=value,
                        state=state,
                        fetched_at=manifest.started_at,
                        source_updated_at=manifest.source_updated_at,
                        artifact_sha256=manifest.artifact_sha256,
                    )
                )
            for child in element.iter():
                native = fields(child)
                if native.get("AttributeCode") and (native.get("ValueCode") or native.get("Value")):
                    observations.append(
                        Observation(
                            interface=self.interface,
                            endpoint=manifest.endpoint,
                            field="attribute:" + native["AttributeCode"],
                            value=native.get("Value", native.get("ValueCode")),
                            fetched_at=manifest.started_at,
                            artifact_sha256=manifest.artifact_sha256,
                        )
                    )
            for container in element:
                if len(container):
                    observations.append(
                        Observation(
                            interface=self.interface,
                            endpoint=manifest.endpoint,
                            field=local(container.tag),
                            value=tostring(container, encoding="unicode"),
                            fetched_at=manifest.started_at,
                            artifact_sha256=manifest.artifact_sha256,
                        )
                    )

            def number(key, values=values):
                if (
                    manifest.endpoint in BASELINE_METHODS
                    and key in PLACEHOLDERS
                    or not values.get(key)
                ):
                    return None
                try:
                    val = Decimal(values[key])
                    if not val.is_finite() or val < 0:
                        raise ValueError()
                    return val
                except (InvalidOperation, ValueError):
                    raise CatalogError("invalid_numeric_field") from None

            item_id = "ed:" + values["ProId"]
            yield SourceItem(
                supplier="ed",
                source_id=values["ProId"],
                sku=values["Code"],
                name=values.get("Name", ""),
                manufacturer=values.get("ProducerName"),
                mpn=values.get("PartNumber"),
                ean=values.get("EANCode"),
                observations=observations,
            )
            unit, with_fees = number("YourPrice"), number("YourPriceWithFees")
            fees = (
                with_fees - unit
                if unit is not None and with_fees is not None and with_fees >= unit
                else None
            )
            qty = number("OnStockCount")
            flag = values.get("OnStock", "").lower()
            stock = "unknown"
            if manifest.endpoint not in BASELINE_METHODS:
                if qty is not None:
                    stock = "in_stock" if qty > 0 else "out_of_stock"
                elif flag in {"true", "1", "false", "0"}:
                    stock = "in_stock" if flag in {"true", "1"} else "out_of_stock"
            discount_qty = number("ValuePackQty")
            offer = Offer(
                item_id=item_id,
                unit_net=unit,
                fees_net=fees,
                vat_percent=number("Vat"),
                currency=values.get("PriceCurrency"),
                order_multiple=number("MultipleQuantity") or None,
                price_rule="valuepack" if discount_qty and discount_qty > 1 else "plain",
                discount_min_qty=discount_qty or None,
                stock_qty=qty,
                stock_state=stock,
                observations=observations,
                fetched_at=manifest.started_at,
                evidence_at=manifest.started_at,
                source_updated_at=manifest.source_updated_at,
            )
            yield apply_contract(offer, export_values | values, contract, manifest)
            records += 1
            element.clear()
        if not records and manifest.domain != "schema":
            raise CatalogError("invalid_export")
        # Full baselines enumerate identity; details/stock never establish catalog completeness.
        manifest.complete = records > 0 and manifest.endpoint in (
            {"getProductListDownloadXML", "getProductListDownloadZIP", "getProductList"}
            | BASELINE_METHODS
        )
