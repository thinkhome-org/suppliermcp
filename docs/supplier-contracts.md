# Supplier contracts

Fixtures in tests are synthetic examples derived from the supplied documentation,
not authenticated captures. Account capability coverage remains unverified.

For eD, PUBLIC identity and price fields are eligible observations. PRIVATE basic
catalog price, fee, VAT and stock fields are placeholders. Detailed and stock
exports contain eligible offers, but do not establish whole-catalog identity
coverage. Compare valid observations by source update time; conflicting values
without comparable timestamps remain conflicts. A generated-file download time is
not its underlying data update time. ValuePack formulas below the qualifying
quantity must be verified before deriving a price. Preserve raw discount terms.

PRIVATE schema/commodity enrichment must be verified against baseline ProIds; a
partial enrichment cannot remove a baseline item. Original supplier codes remain
available even before common attribute mapping exists.

100MEGA contracts are account-specific. Configure supported modes, verified timezone,
allowed weekday/hour lists, coverage and stock representation for each result type.
Unknown schedules fail closed. QtyPack defaults to one in StoItemBase but is not
an order multiple. Missing fee/currency fields stay unknown. Full stocked-only feeds
may reconcile absence only with explicitly verified complete coverage. Delta and
targeted records never imply deletion. ResultTypeInfo and export schemas must be
reviewed before enabling a contract; this application does not guess capability
semantics from an undocumented HTML layout.

## Explicit mappings

`src/suppliermcp/catalog/mappings.json` starts empty. Each verified entry maps a `native:INTERFACE:FIELD` to `{ "field": "capacity_gb", "type": "number", "unit": "GB", "scale": "0.001" }`, for example only when the native value is proven to be decimal MB. Mapping names cannot shadow core offer/identity fields. Invalid numeric values remain unknown. Mapped facts must be reviewed against supplier schema; no manufacturer-web enrichment is used.

PRIVATE refreshes fetch the complete baseline, commodity chunks and schema/relationship dictionaries. Failed chunks preserve the baseline and report partial coverage. Supplier relationships retain declared type, quantity and origin; the documented `ProductRealationParent/Child` spelling is supported. Native navigator attribute codes remain source-scoped. A known `ed:CATEGORY_CODE` is accepted by schema discovery; returned fields still require explicit category filters for product listing.

## Verified offer semantics

An optional `offer` object is supported under each eD interface configuration and under each 100MEGA export contract. Only set values after verifying their meaning with the account supplier. Supported defaults are `order_multiple`, `fees_net`, and `currency`; corresponding `*_field` keys can reference a native product field. Existing direct values take precedence.

`timestamp_field` references a product price-evidence timestamp. Alternatively, `export_timestamp_field` references an export-level timestamp preceding its records. Neither enables freshness unless `timestamp_is_price_evidence` is explicitly `true`: ordinary file generation time is insufficient. `freshness_seconds` supplies the verified validity interval; naive timestamps additionally require a verified IANA `timezone`. Absent settings leave totals/freshness unknown. Example shape, not actual supplier field semantics:

```json
{"offer":{"order_multiple":"1","fees_net":"0","currency":"CZK","timestamp_field":"VerifiedPriceTimestamp","timestamp_is_price_evidence":true,"freshness_seconds":3600}}
```

Mapped common observations preserve source endpoint, artifact hash, time and derivation. Verified packaging mappings therefore feed both typed filtering and conservative product matching. Conflicting mapped values remain unresolved.
