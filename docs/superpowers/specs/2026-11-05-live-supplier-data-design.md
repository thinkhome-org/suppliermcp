# Live supplier data activation

Status: proposed; approach selected by the user, document approval pending. Independent builder check completed: no material unanswered questions.

## Intent and scope

Make the existing SupplierMCP work with the user's actual 100MEGA and eD PUBLIC accounts, using all available product information to improve discovery, filtering, details and per-product comparisons. The user selected complete product data, including parameters, categories, attachments and relationships, through the existing adapters.

The approved v1 design remains authoritative. Supplier access remains read-only. Orders, invoices, claims, customer records, account administration and writes remain excluded, even when their documentation or methods are discoverable. eD PRIVATE remains optional and disabled: document its interfaces, preserve compatibility, but do not claim authenticated validation without access. No manufacturer-site enrichment, procurement optimization or public tunnel is added.

## Approaches

1. **Selected: complete product ingestion through existing adapters.** Extend the current transport, parsers, publication, schema and index paths with verified supplier-specific contracts. Preserve every supplied product field with provenance; normalize only established semantics. More work than the minimal repair, but provides the requested search coverage and continues working during supplier outages.
2. **Rejected by the user: repair baseline catalog, prices and stock only.** Smaller change, but leaves supplied parameters, categories and relationships unused.

No new service or replacement architecture is needed. Keep PostgreSQL authoritative, Typesense rebuildable, existing MCP tools and English repository content.

## Evidence from initial live reconnaissance

Authenticated 100MEGA capability discovery succeeded from this machine on 2026-11-05. It advertises 65 export families / 120 named variants, including excluded business-document interfaces. Product-related schema reconnaissance fetched 94 schema responses: 89 actual schemas, four HTTP 500 responses and one empty Result instead of a schema. Advertisement is not proof that a data export succeeds.

The stock export returned 33,431 rows. Targeted price, currency-price, parameter, EAN, packaging and relationship requests succeeded for one source-selected SKU; the relationship response was empty and does not validate nonempty relationship handling. The price response uses `PriceOrd`, not the current parser's `PriceDea`. The currency-price response places `CurCode` on the root. Parameters use `Row` records keyed by `StiId`/`StiCode`, rather than `StoItem`.

The account advertises different windows for each method, including targeted methods. For example, full StoItemBase permits hours 21–07, while its targeted mode permits 21–06; targeted StoItemQtyFree has a different window again. Use the live account matrix, not the less precise email summary. Europe/Prague is an implementation proposal based on the Czech service; verify server behavior at window boundaries and retain the evidence basis in configuration. Do not bypass a restricted full export by enumerating targeted requests.

The existing Codex edshop connector successfully requested an eD PUBLIC XML export. Its existing local environment file supplies the credentials. The live SOAP response uses `url`, `fileName`, `isReady`; the adapter currently expects capitalized names and incorrectly accepts the status envelope as an empty import. The complete XML download is 619,833,546 bytes and the existing record parser reads 124,532 SourceItems and 124,532 Offers in 26.26 seconds. The current 256 MiB transport default and in-memory buffering are unsuitable. This parser check does not prove database publication or MCP availability.

Raw captures and secrets stay outside Git. Committed evidence contains endpoint names, schema structure, counts, hashes, statuses and sanitized fixtures, never account-bearing export URLs, credentials or private commercial prices.

## Endpoint and field inventory

Produce an English machine-readable inventory plus a readable matrix. Cover every advertised endpoint/variant with one explicit classification: product ingestion, equivalent serialization, product integration unavailable, excluded by v1, or unverified. Include method parameters, account windows, schema fields/types, parent-child structure, join keys and the source of each semantic mapping. Track advertised, schema-read, data-read, parsed, published and MCP-validated separately.

For eD PUBLIC, use one canonical complete XML/ZIP representation for ingestion; test the documented product variants and record their equivalence or differences. Do not repeatedly ingest equivalent serializations. Extract commodity codes/names and all supplied fields. PUBLIC does not imply PRIVATE navigator access. PRIVATE WSDL and supplied documentation receive an inventory only.

For 100MEGA, cover baseline/active identities, prices and currency, stock/availability, EANs, category and presentation trees, product-tree memberships, parameter definitions and values, packaging, images/attachments, relationships, variants and other account-available product exports. `_El` encodings and special exports are mapped and probed where permitted; ingest a canonical representation when equivalent. Preserve additional unique product information from special exports with explicit join semantics. Unknown or failed exports must remain visible coverage gaps, never silent successes.

## Import and storage behavior

1. Stream downloads into the existing artifact store with bounded byte counts, hashes and atomic completion. Keep hostname/DNS pinning, TLS validation, redirect checks, credential isolation and operation allowlists. Retrying a partial download must restart a fresh artifact. Use the documented ZIP option where beneficial, with bounded streaming decompression. Set actual account limits based on measured catalog sizes with headroom, not an arbitrary small cap. No silent truncation.
2. Parse records incrementally and release processed XML nodes. Publish only a completely parsed, validated import. Status/envelope-only responses must fail visibly; valid empty enrichment is distinct from a missing catalog. Preserve raw supplier fields and nested records, including root metadata needed for URLs and currency.
3. Separate authoritative identity snapshots from price, stock and enrichment records. An enrichment row cannot erase name/manufacturer, establish catalog completeness or mark a product removed. Only verified full identity snapshots reconcile presence. Use stable source keys; relationships retain direction, type and quantity.
4. Add endpoint-aware checkpoints, publication authority and coverage where the current domain-only structure would collide across multiple enrichment exports. A failure preserves the previous successful data for that endpoint. A successful complete enrichment replaces its prior contribution, including removed parameter values, without erasing other endpoints. Delta removal semantics require explicit proof; otherwise retain uncertainty.
5. Preserve multi-valued parameters as sets of separately identifiable supplier facts. Do not mistake valid multiple values for conflicting single-value observations. Native filters must match set membership; common numeric fields require verified units and definitions. New common mappings follow supplier evidence, never name-based guesses.
6. Validate the actual import's database and index costs. Use bounded batches/bulk operations in existing paths where per-row work makes full catalogs impractical. No architecture change merely for hypothetical scale. Record elapsed time, peak memory where measurable, counts and index completeness.

## Price and availability semantics

Use account price fields, distinguish dealer/reference/retail amounts and preserve their original names. Root currency is propagated only to its export's records. Do not sum unknown fees as zero or equate package count with order multiple. Verify `NonDivQty`, fee omission and other candidate defaults before assigning common semantics; retain unknown values otherwise.

Price evidence time, source-generation time and download time remain separate. An authenticated read does not make a cached price current. Keep last-known prices and their age/uncertainty visible. Preserve eD ValuePack conditions without guessing the undisclosed discount formula. Stock-only exports must handle absent products only according to verified feed scope.

## Search and MCP behavior

All available product facts must be accessible through existing discovery, listing, schema and detail tools. Preserve source-specific category trees and parameter names/IDs; expose usable native fields even without a cross-supplier mapping. Index useful supplied names, descriptions, parameters and categories. Do not fetch third-party manufacturer content from attachment links.

Keep seven tool names and existing calls compatible. If a full detail exceeds the response budget, extend `get_product` with optional section selection and stable pagination for observations, attachments and relationships; the ordinary detail returns a compact overview with continuation information. Every fact must be reachable without silently truncating it. Use the existing principal/cursor protections. Update built-in skills to explain category/parameter discovery, continuation and incomplete-source results.

## Local activation

Configure the persistent local Docker stack for eD PUBLIC and 100MEGA only. Reuse the existing eD secret source and supplied 100MEGA email locally. Secrets/configuration are protected outside Git and passed through existing environment/mount mechanisms. Do not modify the existing edshop connector. Provide a local authenticated MCP endpoint and a usable Codex configuration; keep signing material separate from the server and credentials out of plugin artifacts. Public URL/tunnel work stays deferred.

Schedules honor per-export/per-method windows. Pending night-only exports are visible and resumed in the permitted window, without tight retry loops. Test unconfigured interfaces, temporary authentication/network failure, missing optional exports, unchanged data, recovery and index loss against a separate test database or controlled failure injection. Never destroy the persistent live catalog to run a test.

## Acceptance and truthful completion

- Inventory accounts for all advertised interfaces and all schema fields; every excluded or unsupported item has a reason.
- Complete permitted catalogs and unique enrichment are downloaded, parsed, published and queryable, with counts reconciled at each stage. Source-side empty/error/restricted responses are reported separately.
- Representative exact SKU/EAN/MPN lookups, Czech/English text searches, native parameter/category filters and per-product price comparisons are checked against captured live evidence through the authenticated MCP endpoint and Codex.
- Paginate full filtered results and large product details without gaps or duplicates; verify preservation of leading-zero identifiers, multi-valued parameters and nested relationships.
- Confirm price/currency/fees/quantity semantics using actual exports; unknown semantics remain explicit and do not produce invented totals or freshness.
- Verify resilience without supplier writes and without interfering with the existing edshop connector.
- Run focused regression tests, the full repository suite, lint, Docker startup/restart persistence and actual client checks. Capture test dates, sizes, counts and unresolved supplier limitations in `docs/validation.md` and the endpoint matrix.
- Restricted exports are not called outside their windows. If a required window or supplier failure prevents validation, report the work as incomplete at that layer and retain a reproducible next step. Do not claim that all live functionality works from schema discovery alone.

## Builder discretion

The implementer chooses the smallest compatible schema migration, batching strategy, snapshot naming and scheduling details supported by measurements. Optional detail-pagination parameters and native field identifiers must be documented and regression-tested. Do not add another database, search engine, queue service or general web scraper. Preserve existing user decisions and expose evidence gaps rather than manufacturing semantics.
