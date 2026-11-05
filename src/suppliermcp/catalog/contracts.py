"""Validated data at supplier, persistence and MCP boundaries."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Interface = Literal["ed_public", "ed_private", "mega"]
Domain = Literal["catalog", "price", "stock", "schema"]
RunMode = Literal["full", "delta", "targeted"]
Money = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
Positive = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CatalogError(Exception):
    def __init__(self, code: str, message: str = "", retryable: bool = False):
        self.code, self.message, self.retryable = code, message or code, retryable
        super().__init__(self.message)

    def as_dict(self):
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


class Observation(Model):
    value_type: Literal["text", "number"] = "text"
    value_key: str = ""
    cardinality: Literal["one", "many"] = "one"
    interface: Interface
    endpoint: str
    field: str
    value: Any = None
    unit: str | None = None
    state: Literal["known", "missing", "placeholder", "conflict", "not_applicable"] = "known"
    fetched_at: datetime = Field(default_factory=utcnow)
    source_updated_at: datetime | None = None
    artifact_sha256: str = ""
    derivation: Literal["direct", "mapped"] = "direct"


class SourceItem(Model):
    supplier: Literal["ed", "mega"]
    source_id: str
    sku: str
    name: str
    manufacturer: str | None = None
    mpn: str | None = None
    ean: str | None = None
    observations: list[Observation] = Field(default_factory=list)

    @property
    def item_id(self):
        return f"{self.supplier}:{self.source_id}"


class Offer(Model):
    item_id: str
    currency: str | None = None
    unit_net: Money | None = None
    fees_net: Money | None = None
    vat_percent: Money | None = None
    order_multiple: Positive | None = None
    price_rule: Literal["plain", "valuepack", "unknown"] = "plain"
    discount: Money | None = None
    discount_min_qty: Positive | None = None
    stock_qty: Money | None = None
    stock_state: Literal["in_stock", "out_of_stock", "unknown"] = "unknown"
    observations: list[Observation] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=utcnow)
    source_updated_at: datetime | None = None
    evidence_at: datetime = Field(default_factory=utcnow)
    stock_evidence_at: datetime | None = None
    refresh_failed: bool = False
    freshness_seconds: int | None = Field(default=None, gt=0)


class Capabilities(Model):
    domains: list[Domain] = Field(default_factory=list)
    endpoints: dict[str, list[RunMode]] = Field(default_factory=dict)
    windows: dict[str, Any] = Field(default_factory=dict)
    coverage: Literal["complete", "partial", "unknown"] = "unknown"
    freshness_seconds: dict[str, int] = Field(default_factory=dict)


class BatchManifest(Model):
    authoritative_identity: bool | None = None
    replace_scope: Literal["none", "items", "endpoint"] = "none"
    interface: Interface
    domain: Domain
    mode: RunMode = "full"
    endpoint: str = ""
    path: str = ""
    artifact_sha256: str = ""
    source_updated_at: datetime | None = None
    started_at: datetime = Field(default_factory=utcnow)
    capabilities: Capabilities = Field(default_factory=Capabilities)
    complete: bool = False
    stock_only: bool = False
    delta_from: datetime | None = None
    delta_to: datetime | None = None


class SchemaRecord(Model):
    interface: Interface
    kind: str
    values: dict[str, Any]


ParsedRecord = SourceItem | Offer | SchemaRecord


class ImportBatch(BatchManifest):
    items: list[SourceItem] = Field(default_factory=list)
    offers: list[Offer] = Field(default_factory=list)


class Identifier(Model):
    kind: Literal["sku", "ean", "mpn"]
    value: str = Field(min_length=1)
    supplier: Literal["ed", "mega"] | None = None
    manufacturer: str | None = None

    @model_validator(mode="after")
    def context(self):
        if self.kind == "sku" and not self.supplier:
            raise ValueError("SKU requires supplier")
        if self.kind == "mpn" and not self.manufacturer:
            raise ValueError("MPN requires manufacturer")
        return self


class QuantityRequest(Model):
    quantity: Positive = Decimal(1)


class Filter(Model):
    field: str
    operator: Literal["eq", "in", "gte", "lte"]
    value: Any


class CatalogQuery(Model):
    source_id_from: str | None = None
    source_id_to: str | None = None
    filters: list[Filter] = Field(default_factory=list)
    classification: Literal["confirmed", "unknown"] = "confirmed"
    sort: Literal["id", "price_asc", "price_desc"] = "id"
    currency: str | None = None
    supplier: Literal["ed", "mega"] | None = None

    @model_validator(mode="after")
    def price_currency(self):
        if self.sort != "id" and not self.currency:
            raise ValueError("Price sorting requires a currency")
        return self


class Coverage(Model):
    interfaces: dict[str, Any] = Field(default_factory=dict)
    revision: int = 0
    index_revision: int = 0
    complete: bool = False
    warnings: list[str] = Field(default_factory=list)


class ProductView(Model):
    detail_continuation: dict | None = None
    product_id: str
    item: SourceItem
    offers: list[Offer] = Field(default_factory=list)
    relationships: list[dict] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class Page(Model):
    results: list[ProductView] = Field(default_factory=list)
    total: int = 0
    unknown_total: int = 0
    coverage: Coverage = Field(default_factory=Coverage)
    next_cursor: str | None = None
    snapshot_id: str | None = None
    expires_at: datetime | None = None


class LookupResult(Model):
    entries: list[dict] = Field(default_factory=list)
    coverage: Coverage = Field(default_factory=Coverage)


class SearchResult(Page):
    exhaustive: Literal[False] = False


class OfferQuote(Model):
    item_id: str
    requested_qty: Positive
    orderable_qty: Positive
    unit_net: Money | None = None
    total_net: Money | None = None
    currency: str | None = None
    fresh: bool = False
    evidence_at: datetime
    shipping_included: bool = False
    reasons: list[str] = Field(default_factory=list)


class Comparison(Model):
    product_id: str | None = None
    error: dict | None = None
    offers: list[OfferQuote] = Field(default_factory=list)
    last_known_winner: str | None = None
    fresh_winner: str | None = None
    warnings: list[str] = Field(default_factory=list)
