from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

from suppliermcp.catalog.contracts import (
    BatchManifest,
    Capabilities,
    CatalogError,
    Observation,
    Offer,
    SourceItem,
)
from suppliermcp.suppliers.offer_contract import apply_contract, import_projection
from suppliermcp.suppliers.registry import resolve_operation
from suppliermcp.sync.artifacts import parse_xml

from .capabilities import require_window, verified_export_window
from .exports import PRODUCT_EXPORTS, nested_facts, normalize_record
from .exports import values as record_values


class MegaAdapter:
    max_expanded_bytes = 1024**3
    max_description_bytes = 2 * 1024**2
    interface = "mega"
    endpoints = {"catalog": "StoItemBase", "stock": "StoItemQtyFree", "price": "StoItemPriceOrd"}

    def __init__(
        self, transport=None, store=None, contracts=None, base_url="https://i6ws.100mega.cz"
    ):
        self.transport, self.store = transport, store
        self.contracts, self.base_url = contracts or {}, base_url
        self.endpoints = dict(type(self).endpoints)
        if "StoItemPriceOrdCur" in self.contracts:
            self.endpoints["price"] = "StoItemPriceOrdCur"

    def discover(self):
        return Capabilities(
            domains=[d for d, e in self.endpoints.items() if e in self.contracts],
            endpoints={e: c.get("modes", []) for e, c in self.contracts.items()},
            windows={
                e: {k: c.get(k) for k in ["timezone", "days", "hours", "windows"]}
                for e, c in self.contracts.items()
            },
            coverage="partial" if self.contracts else "unknown",
        )

    def export_window(self, endpoint, mode):
        try:
            spec = resolve_operation(f"mega.{endpoint}.{mode}")
        except CatalogError:
            return {}
        return verified_export_window(spec, self.contracts.get(endpoint, {}))

    def fetch(self, domain, codes=None):
        endpoint = self.endpoints.get(domain)
        if not endpoint:
            raise CatalogError("unsupported_domain")
        return self.fetch_export(endpoint, codes=codes)

    def fetch_export(self, endpoint, *, codes=None, from_time=None, to_time=None):
        from suppliermcp.catalog.contracts import utcnow

        if endpoint not in PRODUCT_EXPORTS:
            raise CatalogError("operation_not_allowed")
        if bool(from_time) != bool(to_time) or codes and from_time:
            raise CatalogError("invalid_export_range")
        mode = "targeted" if codes else "delta" if from_time else "full"
        contract = self.export_window(endpoint, mode)
        require_window(contract, mode)
        if codes and len(codes) != 1:
            raise CatalogError("unsupported_targeted_read")
        params = {"resultType": endpoint}
        method = {"full": "GetResult", "targeted": "GetResultByCode", "delta": "GetResultByFromTo"}[
            mode
        ]
        if codes:
            params["code"] = codes[0]
        if from_time:
            if from_time.tzinfo is None or to_time.tzinfo is None or from_time >= to_time:
                raise CatalogError("invalid_export_range")
            params.update({"from": from_time.isoformat(), "to": to_time.isoformat()})
        domain = next((d for d, e in self.endpoints.items() if e == endpoint), "schema")
        manifest = BatchManifest(
            interface="mega",
            requested_skus=codes or [],
            started_at=utcnow(),
            domain=domain,
            mode=mode,
            endpoint=endpoint,
            capabilities=self.discover(),
            authoritative_identity=endpoint in {"StoItemBase", "StoItemBase_El"},
            replace_scope="none" if mode == "delta" else "items" if codes else "endpoint",
            delta_from=from_time,
            delta_to=to_time,
        )
        self.transport.download(
            f"{self.base_url}/Default.asmx/{method}?{urlencode(params)}",
            self.store,
            manifest,
            endpoint=method,
            before_request=lambda: require_window(contract, mode),
        )
        return manifest

    def parse(self, manifest):
        export_values = {}
        contract = self.contracts.get(manifest.endpoint, {})
        offer_contract = contract.get("offer", {})
        root_seen = False
        root_values = {}
        root_container = []

        def remember_root(root):
            root_values.clear()
            root_values.update(root.attrib)
            export_values.clear()
            root_container[:] = [root]

        for element in parse_xml(
            Path(manifest.path),
            max_expanded=self.max_expanded_bytes,
            on_root=remember_root,
            projection=lambda name: import_projection(manifest, name, offer_contract),
        ):
            tag = element.tag.rsplit("}", 1)[-1]
            if tag == offer_contract.get("export_timestamp_field"):
                export_values[tag] = element.text
            if (
                tag == "Result"
                or tag == "SHOP"
                and manifest.endpoint in {"StoItemShop_El", "StoItemShoptet_El"}
            ):
                root_seen = True
            if tag == "StoItem" and root_container and element not in root_container[0]:
                continue
            if tag != "StoItem":
                if tag not in {"Result", "SHOP"} and (
                    tag == "Row" or root_container and element in root_container[0]
                ):
                    if not element.attrib and not len(element):
                        root_values[tag] = element.text or ""
                    else:
                        yield from normalize_record(manifest, element, root_values)
                        element.clear()
                continue
            values = record_values(element)
            if not values:
                element.clear()
                continue
            if manifest.domain == "schema":
                yield from normalize_record(manifest, element, root_values)
                element.clear()
                continue
            if not values.get("Id") or not values.get("Code"):
                raise CatalogError("missing_product_identity")
            if manifest.endpoint == "StoItemBase":
                values.setdefault("QtyPack", "1")
            if any(len(str(v).encode()) > self.max_description_bytes for v in values.values()):
                raise CatalogError("description_too_large")
            observations = [
                Observation(
                    interface="mega",
                    endpoint=manifest.endpoint,
                    field=k,
                    value=v,
                    fetched_at=manifest.started_at,
                    source_updated_at=manifest.source_updated_at,
                    artifact_sha256=manifest.artifact_sha256,
                )
                for k, v in values.items()
            ]

            def num(key, values=values):
                value = values.get(key)
                if value is None:
                    return None
                try:
                    result = Decimal(value)
                    if not result.is_finite() or result < 0:
                        raise ValueError()
                    return result
                except (InvalidOperation, ValueError):
                    raise CatalogError("invalid_numeric_field") from None

            observations.extend(nested_facts(manifest, element))
            observations.extend(
                Observation(
                    interface="mega",
                    endpoint=manifest.endpoint,
                    field="root:" + k,
                    value=v,
                    fetched_at=manifest.started_at,
                    artifact_sha256=manifest.artifact_sha256,
                )
                for k, v in root_values.items()
            )
            yield SourceItem(
                supplier="mega",
                source_id=values["Id"],
                sku=values["Code"],
                name=values.get("Name", ""),
                manufacturer=values.get("ManName"),
                mpn=values.get("PartNo"),
                ean=values.get(contract.get("ean_field", "EAN")),
                observations=observations,
            )
            qty = num("QtyFree")
            state = "unknown"
            if qty is not None:
                state = "in_stock" if qty > 0 else "out_of_stock"
            elif "QtyFreeIs" in values:
                state = "in_stock" if values["QtyFreeIs"] == "1" else "out_of_stock"
            elif contract.get("stock_mode") in {"flag", "count"}:
                state = "out_of_stock"
                if contract["stock_mode"] == "count":
                    qty = Decimal(0)
            fees = None
            if "PriceRef" in values and "PriceRef2" in values:
                fees = num("PriceRef") + num("PriceRef2")
            offer = Offer(
                item_id="mega:" + values["Id"],
                unit_net=num("PriceOrd") if "PriceOrd" in values else num("PriceDea"),
                fees_net=fees,
                currency=values.get(
                    contract.get("currency_field", "Currency"),
                    root_values.get("CurCode", contract.get("currency")),
                ),
                vat_percent=num("TaxRate"),
                stock_qty=qty,
                stock_state=state,
                observations=observations,
                fetched_at=manifest.started_at,
                evidence_at=manifest.started_at,
                source_updated_at=manifest.source_updated_at,
            )
            yield apply_contract(offer, export_values | values, offer_contract, manifest)
            element.clear()
        if not root_seen:
            raise CatalogError("unexpected_export_root")
        manifest.complete = manifest.mode == "full" and contract.get("coverage") == "complete"
        manifest.stock_only = bool(contract.get("stock_only"))
