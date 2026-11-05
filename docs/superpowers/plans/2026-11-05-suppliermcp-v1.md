# SupplierMCP v1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The user selected inline execution, with a fresh whole-branch review at the end. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a read-only catalog MCP for Codex with optional eD PUBLIC, eD PRIVATE and 100MEGA connections, reliable filtering and quantity-aware per-product offers.

**Architecture:** PostgreSQL owns normalized observations and current offers; Typesense is a rebuildable discovery index. A shared Python application runs as an HTTP MCP server and a separately scheduled worker. Source-specific contracts preserve uncertainty and protect the last successful state.

**Tech Stack:** Python 3.12, uv, FastMCP, Pydantic 2, HTTPX, Zeep where WSDL binding is needed, defusedxml for export parsing, psycopg 3, SQL migrations, Procrastinate, PostgreSQL 18, Typesense, pytest and Ruff. Exact compatible Python dependencies go in uv.lock; Docker base images and services are pinned by digest at execution, not to an unverified version inferred from this plan.

**Spec:** `docs/superpowers/specs/2026-11-05-suppliermcp-v1-design.md` (approved 2026-11-05).

## Global Constraints

- Integrate eD PUBLIC, eD PRIVATE and 100MEGA I6WS. Each interface is optional; any combination must work.
- One company account per supplier. PUBLIC and PRIVATE enrich the same eD supplier, not separate competing offers.
- Products and offers only: no order submission or changes, and no reading orders, invoices, deliveries or claims in v1.
- No whole-basket optimization and no user-facing price history.
- Display last-known prices during outages, explicitly identifying age and inability to refresh.
- Use supplier data exclusively, including future versions. No manufacturer-web research or model-invented product facts.
- Primary client: Codex. Docker deployment and an HTTP MCP URL; tunnel and actual deployment are outside this design's delivery scope.
- All authored repository content is English. Preserve supplier text in its original language.
- Leave room for semantic retrieval later; embeddings and an internal LLM are not v1 dependencies.
- Prices and quantities use decimal arithmetic, never binary floating point.
- Essential correctness cannot depend on skills being loaded.

## Review Focus

1. Out-of-order concurrent refreshes must not regress current offers or index documents (Tasks 5 and 8).
2. A stale index can omit new matches even after database hydration; discovery must report lag without claiming completeness (Task 8).
3. Result handles must bind query parameters and authorization identity; changed filters or another identity cannot reuse them (Tasks 7 and 9).
4. An unchanged supplier-generated file downloaded again must not become a freshly verified price (Tasks 3, 4 and 6).
5. XML errors, signed download URLs and nested exceptions must not leak account secrets or enable network/file access (Tasks 2 and 9).

---

## Scope, execution and file ownership

This is one dependent catalog application, not independent subprojects. Execute Tasks 1–11 in order on an isolated implementation branch/worktree; the current repository contains only the approved design. No push, merge, installation into the user's Codex configuration, tunnel setup or supplier-account changes are part of execution.

Task files below are exact planned paths, all new unless marked Modify. Use `src/suppliermcp/` as the import package. Add package markers where needed, not abstraction-only modules. Keep code and fixture changes with their owning task. Tests use real PostgreSQL/Typesense in integration tests, mock HTTP at the adapter boundary, and never silently skip missing integration infrastructure.

Dependency gate in Task 1: resolve stable compatible releases supporting Python 3.12 and Streamable HTTP, record exact versions and tested MCP protocol in `docs/compatibility.md`. Avoid mandatory experimental extensions. If no compatible release exists, ledger the smallest spec-preserving adjustment before implementation. Verify APIs from installed packages rather than copying current online examples blindly.

Default limits (engineering decisions): 50 lookup/compare items; page size 20, maximum 100; 30-minute result TTL; 100,000 materialized rows per result; 256 KiB tool response; 30-second supplier HTTP timeout; three read attempts with capped backoff and Retry-After; one concurrent request per supplier. 256 MiB compressed and 1 GiB expanded export limits, maximum 100 ZIP members, 2 MiB per product description. Configurable limits fail visibly, never truncate silently. Retain the newest successful artifact per interface/domain plus failed artifacts for 7 days, with a 5 GiB overall artifact budget. Reject new imports rather than deleting pinned/in-use artifacts to fit the budget.

### Shared contract vocabulary

Define these in Task 1 in `catalog/contracts.py`; later tasks extend no incompatible fields without a ledgered ruling. Pydantic models forbid unknown input fields and reject NaN/Infinity, negative prices, and nonpositive quantities. Serialize Decimal as strings and timestamps as UTC ISO 8601.

- `Interface`: `ed_public | ed_private | mega`; `Domain`: `catalog | price | stock | schema`; `RunMode`: `full | delta | targeted`.
- `Observation`: `interface`, `endpoint`, `field`, `value` (JSON-safe scalar), `unit: str | None`, `state: known | missing | placeholder | conflict | not_applicable`, `fetched_at`, `source_updated_at: datetime | None`, `artifact_sha256`, `derivation: direct | mapped`.
- `SourceItem`: `supplier: ed | mega`, `source_id`, `sku`, `name`, `manufacturer: str | None`, `mpn: str | None`, `ean: str | None`, `observations: list[Observation]`. Identifiers stay strings.
- `Offer`: `item_id`, `currency: str | None`, `unit_net: Decimal | None`, `fees_net: Decimal | None`, `vat_percent: Decimal | None`, `order_multiple: Decimal | None`, `price_rule: plain | valuepack | unknown`, `discount: Decimal | None`, `discount_min_qty: Decimal | None`, `stock_qty: Decimal | None`, `stock_state: in_stock | out_of_stock | unknown`, plus observations. Discount unit/formula must be established before normalizing to a Decimal monetary discount.
- `Capabilities`: supported domains and result types, supported modes per endpoint, allowed windows/timezone, `coverage: complete | partial | unknown`, freshness intervals or unknown.
- `ImportBatch`: interface/domain/mode, items/offers, capabilities, artifact identity, source time, run start, completeness evidence, delta window; use streamed staging for large catalogs rather than holding a whole batch in memory. `BatchManifest` is its metadata; `ParsedRecord = SourceItem | Offer` is the streamed row.
- `Identifier`: kind `sku | ean | mpn`, value, optional supplier/manufacturer; require supplier for SKU and manufacturer for MPN.
- `Filter`: field, operator `eq | in | gte | lte`, typed value; category-scoped schema determines legal operators and units.
- `CatalogQuery`: filters, classification `confirmed | unknown`, sort `id | price_asc | price_desc`, optional currency (required for price sorting), optional supplier.
- `Coverage`: per-interface configuration/outcome, catalog revision, index revision, observation times, `complete: bool`, warnings. A revision is a monotonically increasing database sequence.
- `CatalogError`: code, safe message, retryable, details containing no supplier payload or credentials.
- `ProductView`: stable product/source IDs, identifiers, name, observations, current offers, relationships and conflict reasons; must retain source identities even when grouped.
- `Page`: results, total, unknown_total, coverage, next_cursor, snapshot_id, expires_at. `LookupResult`: one entry per input with `found | missing | ambiguous | error` and matching ProductViews. `SearchResult`: candidate ProductViews, coverage, continuation and `exhaustive=false`. `Comparison`: per-product offer results, explicit rounded quantities, monetary basis, last_known_winner and fresh_winner (each nullable).

### Endpoint authority and completeness rules

Encode this table in `suppliers/ed/authority.py` and document it in `docs/supplier-contracts.md`. Never choose a whole endpoint as authoritative for every field.

| Endpoint | Eligible fields | Exclusions / reconciliation |
|---|---|---|
| PUBLIC getProductList and XML/ZIP equivalents, onStock=false | Identity, descriptions, categories, price/fees/ValuePack, currency and stock flag | Full account catalog baseline only after complete successful parse; stock flag is not a count |
| PRIVATE getProductCatalogueDownloadXML/ZIP | Identity, basic descriptive fields and baseline IDs | All documented starred price, fee, VAT and stock zero fields are placeholders; cannot replace observations |
| PRIVATE getProductDetail and full commodity exports | Detailed fields, navigator memberships, packaging, relationships where returned, offers | Detail is targeted; commodity chunks are only complete over their declared domains; compare enriched IDs against baseline |
| PRIVATE getProductCatalogueStockDownloadXML / short export | Documented offer fields, quantity, availability date | Date 1900-01-01 is unknown; absence does not imply out-of-stock without verified endpoint contract |
| PRIVATE getNavigator and supporting category/producer/commodity methods | Source schema and dictionaries | Retain native codes; mapping to common fields is explicit and versioned |
| PRIVATE getProductRelationList | Supplier-declared product relationships | Preserve relationship type and origin, never infer compatibility beyond the declaration |
| I6WS StoItemBase | Identity, descriptions, base offer fields per schema | QtyPack omitted means 1, not necessarily an order multiple; omit numeric zero only where documented |
| I6WS StoItemQtyFree | Stock count OR availability flag, depending on schema | Validated full stocked-only export reconciles absent known items to out-of-stock; delta/targeted does not |
| I6WS StoItemPriceOrd | Account price fields documented by actual export schema | Currency/fees remain unknown unless explicitly provided or verified account contract establishes them |

Keep latest valid observation per interface/endpoint/field. Source timestamps order comparable observations; do not equate generation time with underlying product freshness. Different values without comparable timestamps become conflicts, not arbitrary winners. Identical artifact hashes do not reset evidence freshness. New transport fetch times remain recorded separately. A newer invalid/placeholder observation never erases valid last-known evidence. PUBLIC/PRIVATE combine by ProId; conflicting SKU/ID evidence is quarantined, not silently merged.

## Task 1: Establish a runnable configuration and contract foundation

**Files:** Create `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`, `src/suppliermcp/__init__.py`, `config.py`, `catalog/contracts.py`, `tests/test_contracts.py`, `docs/compatibility.md`.

**Interfaces:** Produces `Settings.from_env() -> Settings` and the contract models above. Settings contains optional credentials for each interface, PostgreSQL DSN, Typesense URL/key, artifact directory, limits and MCP authentication settings. Secrets are excluded from repr/serialization. Partial credentials are configuration errors, not silent disconnection.

- [ ] **Step 1:** Create package/test metadata, resolve and lock dependencies; record actual SDK/protocol capabilities. Run `uv sync --locked`. Expected: successful install of the locked environment; no product behavior yet.
- [ ] **Step 2:** Write `test_contracts.py` with eight interface combinations, absent/partial credentials, Decimal serialization, invalid quantities and identifier preservation. Required assertions include:
```python
assert Settings.from_env().enabled_interfaces == []  # empty controlled environment
assert Identifier(kind="sku", supplier="mega", value="00123").value == "00123"
assert offer.model_dump(mode="json")["unit_net"] == "0.10"
assert "supplier-password" not in repr(settings)
# pytest.raises(ValidationError): quantity=0, Decimal('NaN'), missing MPN manufacturer
```
- [ ] **Step 3:** Run `uv run pytest tests/test_contracts.py -q`. Expected: FAIL due to missing contracts/settings behavior.
- [ ] **Step 4:** Implement the contracts and settings, strict validation, stated limits and secret handling. No live calls on import or configuration load.
- [ ] **Step 5:** Run the same test command. Expected: PASS for all eight configurations and validation cases.
- [ ] **Step 6:** Commit the listed files: `git commit -m "feat: define catalog contracts and optional source configuration"`.

## Task 2: Secure supplier transport and bounded artifact storage

**Files:** Create `suppliers/transport.py`, `sync/artifacts.py`, `tests/test_transport.py`, `tests/test_artifacts.py`, `tests/fixtures/security/` (synthetic XML/ZIP fixtures).

**Interfaces:** Consumes Settings/CatalogError. Produces `SupplierTransport.read(method: str, url: str, *, endpoint: str, body: bytes | None = None) -> bytes`, restricted to registered read operations; `ArtifactStore.save(stream: Iterable[bytes], manifest: BatchManifest) -> Path`; `ArtifactStore.prune(now: datetime) -> list[Path]`; `parse_xml(path: Path) -> Iterator[Element]`. Transport is used for SOAP POST reads and GET exports, never generic MCP requests.

- [ ] **Step 1:** Write tests `test_rejects_entity_and_archive_escape`, `test_redirect_checks_every_hop`, `test_dns_rebinding`, `test_retry_budget`, `test_redacts_nested_errors`, `test_retention_protects_active_and_latest`. Assert rejected loopback/IPv6/private redirects, external entities, traversal, exceeded expansion budget and unsafe methods; assert three maximum attempts, Retry-After capped at 60 seconds, and no secret/token query/body in errors. Retention must retain pinned files and fail with `artifact_budget_exceeded` when no safe eviction exists.
```python
assert "secret" not in serialized_error
assert attempts == 3
assert newest_success.exists() and active_artifact.exists()
assert failure.code == "unsafe_download"
```
- [ ] **Step 2:** Run `uv run pytest tests/test_transport.py tests/test_artifacts.py -q`. Expected: FAIL on missing transport/storage.
- [ ] **Step 3:** Implement the interfaces using HTTPX and hardened parsers. Pin validated public destination addresses per connection (TLS hostname validation preserved) or use an equivalently tested transport; do not rely only on preflight DNS. Download hosts and redirect policy are explicit configuration, including WSDL imports. ZIP member paths never become uncontrolled output paths. Credentials go only to their original endpoint, not download redirects. Use atomic temp-file publication, checksums, reference pins and bounded cleanup.
- [ ] **Step 4:** Run the same command. Expected: PASS with no real network access.
- [ ] **Step 5:** Commit: `git commit -m "feat: secure supplier reads and artifact retention"`.

## Task 3: Implement both eD catalog interfaces and their field authority

**Files:** Create `suppliers/ed/public.py`, `private.py`, `authority.py`, `tests/test_ed.py`, `tests/fixtures/ed/`, `docs/supplier-contracts.md`.

**Interfaces:** Consumes transport/artifacts and contracts. Produces `EdPublicAdapter.discover() -> Capabilities`, `EdPrivateAdapter.discover() -> Capabilities`; both implement `fetch(domain: Domain, codes: list[str] | None = None) -> BatchManifest` and `parse(manifest: BatchManifest) -> Iterator[ParsedRecord]`. `merge_ed(observations: list[Observation]) -> list[Observation]` implements the authority table without losing conflicts.

- [ ] **Step 1:** Write synthetic, documentation-derived fixtures for PUBLIC list/download readiness, PRIVATE baseline/detail/stock, navigator, commodity partitions, relationships and supplier error envelopes. Write tests asserting:
```python
assert merged_price == Decimal("125.50")  # PUBLIC valid price survives PRIVATE baseline zero
assert unavailable_date is None          # PRIVATE 1900-01-01
assert source_ids == {"123", "124"}      # includes out-of-stock baseline item
assert repeated_artifact.freshness_evidence_at == original.freshness_evidence_at
assert partition_failure.coverage == "partial"
```
Also test all PUBLIC/PRIVATE combinations, same ProId deduplication, conflicting SKU linkage, two conflicting valid prices, namespaced XML and not-ready polling exhaustion. Save provenance for every parsed field. Document fixture origin, never call fixtures real supplier captures.
- [ ] **Step 2:** Run `uv run pytest tests/test_ed.py -q`. Expected: FAIL for missing adapters/merge.
- [ ] **Step 3:** Implement adapters and table. Use SOAP/WSDL binding only for enumerated catalog reads; enforce the allowlist even if WSDL advertises writes. PRIVATE-only operation obtains baseline IDs, dictionaries and commodity exports; compare enrichment coverage to baseline and preserve unenriched items. Poll readiness within a 120-second job budget; incomplete jobs do not produce complete manifests. Preserve ValuePack raw terms; do not infer an undocumented discount formula.
- [ ] **Step 4:** Run the same command. Expected: PASS, including identical-artifact freshness and placeholder cases.
- [ ] **Step 5:** Commit: `git commit -m "feat: ingest eD PUBLIC and PRIVATE catalog contracts"`.

## Task 4: Implement capability-aware 100MEGA reads

**Files:** Create `suppliers/mega/capabilities.py`, `adapter.py`, `tests/test_mega.py`, `tests/fixtures/mega/`; Modify `docs/supplier-contracts.md`.

**Interfaces:** Produces `MegaAdapter.discover() -> Capabilities`, `fetch(domain: Domain, codes: list[str] | None = None) -> BatchManifest`, `parse(manifest: BatchManifest) -> Iterator[ParsedRecord]`. Consumes the same transport/contracts as Task 3.

- [ ] **Step 1:** Write fixtures for ResultTypeInfo and supported schema responses, StoItemBase, QtyFree count/flag modes, PriceOrd, disabled methods/windows, malformed and repeated exports. Test these assertions:
```python
assert parsed.sku == "000123"
assert parsed_pack == Decimal("1") and parsed_order_multiple is None
assert availability_count is None  # flag-only schema must not invent a count
assert disallowed_request_count == 0
assert unknown_currency is None
```
Test full stocked-only manifest versus delta, absent empty/default fields, changed XML schema, identity fields missing and unchanged artifacts. Unknown result types remain reported; do not fabricate an EAN or category feed.
- [ ] **Step 2:** Run `uv run pytest tests/test_mega.py -q`. Expected: FAIL for missing adapter.
- [ ] **Step 3:** Implement discovery and endpoint-specific parsing. Use only supported GET/POST read exports; never credentials in URLs. Enforce allowed windows with verified source timezone, and mark unknown windows as requiring configuration instead of inventing schedules. Preserve source schema/attributes not yet mapped. Support configured schema-verified category/attribute exports through explicit mappings; absent ones reduce schema coverage. Do not call order endpoints.
- [ ] **Step 4:** Run the same command. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "feat: ingest capability-aware 100MEGA catalog exports"`.

## Task 5: Publish imports atomically and schedule isolated refreshes

**Files:** Create `catalog/db.py`, `catalog/repository.py`, `sync/publish.py`, `sync/jobs.py`, `worker.py`, `migrations/001_catalog.sql`, `migrations/002_jobs.sql`, `compose.test.yaml`, `tests/integration/conftest.py`, `tests/integration/test_sync.py`.

**Interfaces:** Produces `migrate(conn: psycopg.Connection) -> None`, `stage(conn, manifest: BatchManifest, rows: Iterable[ParsedRecord]) -> UUID`, `publish(conn, run_id: UUID) -> int` (catalog revision), `schedule_refresh(interface: Interface, domain: Domain, codes: list[str] | None = None) -> int` (job ID), `read_status(conn) -> Coverage`. No source calls occur inside publication transactions.

- [ ] **Step 1:** Write real-PostgreSQL tests for rollback, replay, per-domain checkpoints, zero/disappearing stock, bad full snapshots, overlapping runs, disabled sources and durable last-known data. Assertions:
```python
assert state_after_failed_import == state_before
assert count_after_replay == count_before_replay
assert stock_after_full_absence == Decimal("0")
assert stock_after_delta_absence == previous_stock
assert revision_after_older_run == revision_after_newer_run
assert current_offer_after_timeout == previous_offer
```
Parameterize eight configured-interface combinations. Include restart between commit and queue delivery; the outbox must survive. A >25% item drop versus last complete catalog quarantines the run; an explicit audited maintenance acceptance is needed to publish it. Test empty full exports as suspicious, not mass deletion.
- [ ] **Step 2:** Start disposable services using `docker compose -f compose.test.yaml up -d --wait`; Expected: healthy PostgreSQL and Typesense with test-only credentials. Run `uv run pytest tests/integration/test_sync.py -q`. Expected: FAIL for missing schema/publication.
- [ ] **Step 3:** Implement SQL migrations under a database lock and psycopg transactions. Tables: source_items, observations (latest per source/field), current_offers, source_schema, relationships, import_runs/staging, domain_checkpoints, source_state, index_outbox; add query tables in Task 7. Serialize source/domain jobs with Procrastinate locks, reject older publication evidence and maintain global revision ordering. Outbox records identify item IDs and revisions; consumers read current state, not outdated payloads. Schedule only supported operations with configured verified intervals/windows; no source means no supplier jobs. Provide maintenance CLI `python -m suppliermcp.worker accept-import RUN_ID --reason TEXT`, with explicit audit metadata, not an MCP tool. Add cleanup of completed jobs/staging and pinned artifacts.
- [ ] **Step 4:** Run the same tests. Expected: PASS including forced failure/rollback and worker restart cases.
- [ ] **Step 5:** Commit: `git commit -m "feat: publish catalog snapshots with durable refresh jobs"`.

## Task 6: Resolve product identity and quantity-aware current offers

**Files:** Create `catalog/matching.py`, `catalog/offers.py`, `migrations/003_product_links.sql`, `tests/test_matching.py`, `tests/test_offers.py`, `tests/integration/test_offer_refresh.py`.

**Interfaces:** Produces `match_items(left: SourceItem, right: SourceItem) -> MatchDecision` (`same | different | unresolved`, evidence), `quote(offer: Offer, quantity: Decimal, now: datetime) -> OfferQuote`, `compare(offers: list[Offer], quantity: Decimal, now: datetime) -> Comparison`. OfferQuote includes requested/orderable quantity, nullable unit/total, currency/basis, freshness, excluded shipping and unknown reasons. Product links preserve original IDs; repository supplies stable ProductViews.

- [ ] **Step 1:** Write exact-identifier plus variant-conflict tests, unknown-packaging cases and monetary tests:
```python
assert match_items(single_module, two_module_kit).verdict != "same"
assert match_items(same_name_only_a, same_name_only_b).verdict == "unresolved"
assert quote(plain_010, Decimal("3"), now).total_net == Decimal("0.30")
assert quote(multiple_5, Decimal("3"), now).orderable_qty == Decimal("5")
assert quote(ambiguous_valuepack, Decimal("1"), now).total_net is None
assert compare(stale_and_fresh, Decimal("1"), now).fresh_winner != stale_id
```
Test VAT absent, known zero fees versus missing fees, fractional quantities, different currencies, no fresh offers, repeated file downloads and timeout refresh. Round monetary display only at currency minor units; retain exact Decimal arithmetic and expose pre-round totals.
- [ ] **Step 2:** Run `uv run pytest tests/test_matching.py tests/test_offers.py tests/integration/test_offer_refresh.py -q`. Expected: FAIL for missing matching/quotation.
- [ ] **Step 3:** Implement conservative matching: EAN or manufacturer+MPN evidence, no known variant/condition/packaging conflict, otherwise unresolved. Missing critical packaging evidence cannot authorize a merge. Unlinking changes relationships, not source IDs. Prices below a ValuePack threshold remain unknown unless a supplier-verified formula determines the undiscounted value; at/above threshold use documented eligible price. Show supplied price and eligibility even if comparison total is unknown. Partition winners by currency/tax basis; return no global winner across partitions. A successful fetch without fresh source evidence is not a newly verified price. Refresh enqueue/read failure preserves old quote plus warning.
- [ ] **Step 4:** Run the same tests. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "feat: compare conservative product matches and current offers"`.

## Task 7: Typed filters, exact lookup and immutable result pages

**Files:** Create `search/schema.py`, `search/exact.py`, `search/listing.py`, `catalog/mappings.json`, `migrations/004_query_results.sql`, `tests/test_filters.py`, `tests/integration/test_listing.py`.

**Interfaces:** Produces `catalog_schema(conn, category: str | None) -> dict`, `lookup(conn, identifiers: list[Identifier]) -> LookupResult`, `start_listing(conn, query: CatalogQuery, principal: str) -> Page`, `next_page(conn, cursor: str, principal: str) -> Page`. Produces `get_product(conn, product_id: str) -> ProductView` in repository. Result handles store a hash of the canonical query, principal, revisions, ordered IDs and materialized display/offer fields.

- [ ] **Step 1:** Write tests for invalid units/operators, null/conflict classification, exact leading-zero codes, ambiguous IDs, out-of-stock items, unknown categories and stable pages. Required assertions:
```python
assert confirmed_ids == reference_confirmed_ids
assert unknown_ids == reference_unknown_ids
assert ids_before_import == ids_after_import  # materialized handle
assert len(all_ids) == len(set(all_ids)) == expected_count
assert expired_error.code == "result_expired"
assert other_principal_error.code == "result_not_found"
```
Include concurrent import during pagination, price sort with missing values last, changed filter/cursor rejection, unsupported currency sort, 100,001 matches and response-size boundaries. All checks use an independently constructed reference set, not the production filter evaluator.
- [ ] **Step 2:** Run `uv run pytest tests/test_filters.py tests/integration/test_listing.py -q`. Expected: FAIL for missing filter/list implementation.
- [ ] **Step 3:** Implement parameterized SQL over an allowlist of schema fields; never interpolate model-provided SQL fragments. Use SQL three-valued semantics explicitly and source-scoped fields for unmapped attributes. Persist a fixed result under a short repeatable-read transaction; release it before responding. Cursors are opaque server-side handles bound to principal/query. On >100,000 rows return `result_too_large`, exact count and deterministic supplier/source-ID partitions to be queried separately; no partial list marked complete. Enforce 256 KiB output by reducing page rows and retaining continuation, or explicit `item_too_large` with separate detail access. Cleanup expires handles and current-offer snapshots after 30 minutes. Exact lookups stay available regardless of Typesense.
- [ ] **Step 4:** Run the same tests. Expected: PASS for reference-set equivalence, consistency and limits.
- [ ] **Step 5:** Commit: `git commit -m "feat: add exact lookup and complete stable catalog filtering"`.

## Task 8: Rebuildable Typesense discovery with database validation

**Files:** Create `search/index.py`, `search/discovery.py`, `search/synonyms.json`, `tests/integration/test_search.py`, `tests/evaluation/queries.json`.

**Interfaces:** Produces `drain_outbox(conn, client) -> int`, `rebuild_index(conn, client) -> str`, `search(conn, client, text: str, filters: list[Filter], principal: str) -> SearchResult`. Consumes authoritative filter evaluation, ProductViews, revisioned outbox and query handles for continuation. Search tools do not accept raw Typesense syntax.

- [ ] **Step 1:** Write tests for partial HTTP-200 imports, replay, tombstones, older concurrent jobs, atomic rebuild, stale false positives, newly missing candidates, accent/case queries and required terms:
```python
assert failed_item_id in pending_outbox_ids
assert newer_revision == indexed_revision_after_old_job
assert violating_item_id not in search_result_ids
assert result.coverage.complete is False  # newer DB revision than index
assert outage_lookup_result == normal_lookup_result
assert all(row.matches_hard_filters for row in returned_candidates)
```
Define 24 synthetic evaluation cases (six per category family from the design), explicit relevant IDs and near-match exclusions; at least eight Czech/English equivalent pairs. Require every known exact code to resolve and all designated must-find IDs within top 20 for discovery cases, without claiming real-catalog recall from synthetic data.
- [ ] **Step 2:** Run `uv run pytest tests/integration/test_search.py -q`. Expected: FAIL for missing index/search behavior.
- [ ] **Step 3:** Implement one serialized indexing lane with row-level acknowledgement and retries; use current DB rows and revision fences. Rebuild into a new collection and swap alias only after complete validated import plus catch-up under the same lane. Index source items so unmatched items never disappear. Treat text as preference and hard attributes as validated filters; disable automatic required-token dropping and code typo substitution. Hydrate and filter candidates in PostgreSQL, disclose indexing lag and any candidate scan budget (initially 1,000). Materialize returned discovery candidates for stable continuation. On Typesense outage return typed `text_search_unavailable` with guidance to exact/list tools; do not fabricate equivalent text search. Do not introduce embeddings now.
- [ ] **Step 4:** Run the same tests and `uv run pytest tests/evaluation -q` (add `tests/evaluation/test_queries.py` to execute the declared cases). Expected: PASS, including all explicit must-find/exclusion cases.
- [ ] **Step 5:** Commit: `git commit -m "feat: add validated text discovery and resilient indexing"`.

## Task 9: Authenticated HTTP MCP with seven typed tools

**Files:** Create `mcp/server.py`, `mcp/tools.py`, `mcp/auth.py`, `mcp/resources.py`, `tests/integration/test_mcp.py`, `tests/test_auth.py`; Modify `config.py`, `docs/compatibility.md`.

**Interfaces:** `create_server(settings: Settings) -> FastMCP`; register `lookup_products(identifiers: list[Identifier]) -> LookupResult`, `search_products(text: str, filters: list[Filter] = [], cursor: str | None = None) -> SearchResult`, `list_products(query: CatalogQuery | None = None, cursor: str | None = None) -> Page`, `get_product(product_id: str) -> ProductView`, `get_catalog_schema(category: str | None = None) -> dict`, `compare_offers(product_ids: list[str], quantities: dict[str, Decimal] = {}, refresh: bool = False) -> list[Comparison]`, `get_catalog_status() -> Coverage`. Use immutable/default-factory equivalents for collection defaults in implementation. Derive principal from verified authentication, never tool arguments.

- [ ] **Step 1:** Through a real HTTP client write tests for discovery, every tool schema, auth, resource access, partial batches, empty catalogs, PostgreSQL/Typesense outages and asynchronous refresh responses:
```python
assert tool_names == {"lookup_products", "search_products", "list_products", "get_product", "get_catalog_schema", "compare_offers", "get_catalog_status"}
assert unauthenticated.status_code == 401
assert expired_token.status_code == 401
assert wrong_audience.status_code == 401
assert catalog_error.code == "catalog_not_populated"
assert db_failure.code == "service_unavailable"
assert "supplier-password" not in response_text
```
Test unsupported writes are absent, resource routes cannot bypass auth, user text cannot execute instructions, and refresh queues a job then returns last-known data with `refresh_pending` rather than blocking for a full export. No hidden uncapped descriptions.
- [ ] **Step 2:** Run `uv run pytest tests/test_auth.py tests/integration/test_mcp.py -q`. Expected: FAIL for missing server/security behavior.
- [ ] **Step 3:** Implement thin wrappers over catalog services and validated structured output. Use FastMCP JWT verification with configured issuer/audience and JWKS or pinned public key, never build an OAuth provider. For local tests generate ephemeral signing keys; repository contains no real token. Refuse server startup without verifier configuration except explicitly isolated test fixtures. Codex receives a bearer token through its environment configuration; OAuth issuance/deployment remains deferred. Validate Origin/Host appropriate to configured endpoint; avoid wildcard trusted hosts. Bind all continuation/resource access to authenticated principal. Provide `catalog://schema`, `catalog://help` and prompts `find-products`/`compare-products`; tool-only access remains sufficient. Liveness reveals no account data; readiness distinguishes unavailable DB from stale sources. Correlate safe errors/logs without logging raw SOAP/XML or token-bearing URLs.
- [ ] **Step 4:** Run the same tests. Expected: PASS with Streamable HTTP and exact seven-tool inventory; record tested protocol and library versions.
- [ ] **Step 5:** Commit: `git commit -m "feat: expose authenticated read-only catalog MCP"`.

## Task 10: Package English skills and reproducible Docker operation

**Files:** Create `skills/product-discovery/SKILL.md`, `skills/offer-comparison/SKILL.md`, `integrations/codex/README.md`, `integrations/codex/mcp.toml.example`, `integrations/codex/build_plugin.py`, `tests/test_packaging.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `README.md`, `docs/operations.md`, `.github/workflows/ci.yml`; Modify `mcp/resources.py`.

**Interfaces:** `build_plugin(source: Path, destination: Path, mcp_url: str) -> Path` builds a deterministic installable package with the two canonical skill folders and remote MCP declaration; no credentials. Skill exposure via MCP reads these same files. Services use `python -m suppliermcp.mcp.server` and `python -m suppliermcp.worker`; migration is an explicit one-shot command.

- [ ] **Step 1:** Write packaging tests for frontmatter/name validation, relative references, symlinks/traversal, identical plugin/MCP skill content, unconfigured-supplier startup, persisted catalog after restart and Compose network isolation. Assert:
```python
assert packaged_skill_bytes == repository_skill_bytes
assert public_service_ports == {"mcp"}
assert "latest" not in pinned_image_references
assert secret_values.isdisjoint(package_contents)
```
Validate plugin manifest against the current documented schema, not a guessed format. A remote skills extension is optional; its absence must not fail tool/plugin acceptance.
- [ ] **Step 2:** Run `uv run pytest tests/test_packaging.py -q`. Expected: FAIL for missing packaging.
- [ ] **Step 3:** Implement package builder and English skills documenting exact/discovery/list distinctions, unknown parameters, quantity comparisons and supplier-only facts. Build the Docker image as a non-root user using uv.lock, health checks and persistent volumes; publish MCP to loopback by default for a future local tunnel, no public DB/index ports. Document authenticated URL connection, disabled sources, migration, backup/restore, index rebuild and import quarantine. Pin image digests and retain single image for both processes. CI runs Ruff, unit/integration/evaluation tests and image smoke checks with synthetic fixtures. No live credentials are required or stored. Do not install the plugin or alter the user's existing Codex configuration.
- [ ] **Step 4:** Run `uv run pytest tests/test_packaging.py -q`, `docker compose config --quiet`, then authenticated disposable Compose smoke with test signing keys. Expected: tests/config pass; catalog survives restart and all eight interface combinations have explicit status.
- [ ] **Step 5:** Commit: `git commit -m "feat: package Codex skills and Docker services"`.

## Task 11: Verify the complete application and record production gates

**Files:** Create `tests/evaluation/test_workflows.py`, `tests/integration/test_resilience.py`, `docs/validation.md`; Modify `docs/compatibility.md`, `README.md`.

**Interfaces:** Consumes all seven MCP tools and the packaged skills. No new product interface.

- [ ] **Step 1:** Add failing whole-flow tests for an interrupted import followed by recovery, source disconnection while cached offers remain, same-generation downloads, index failure followed by repair, pagination during updates, and quote uncertainty. Assertions:
```python
assert recovered_exact_ids == original_exact_ids | newly_imported_ids
assert stale_price_visible and not stale_price_claimed_current
assert confirmed_filter_violations == 0
assert duplicate_page_ids == 0 and skipped_page_ids == 0
assert supplier_write_requests == []
```
- [ ] **Step 2:** Run `uv run pytest tests/integration/test_resilience.py tests/evaluation/test_workflows.py -q`. Expected: FAIL for any integration gap; if already green, record that existing components satisfy these new acceptance cases rather than fabricating a failure.
- [ ] **Step 3:** Resolve any integration defects in owning modules with focused regression tests. Run Codex tool-only and plugin-assisted sessions against the synthetic catalog in an isolated temporary configuration/profile, with explicit scenarios: exact SKU, Czech text query, unknown parameter, stale cheap offer and unavailable source. Record actual tool traces and outcomes without secrets. Do not treat MCP Inspector alone as proof of Codex behavior. If a real Codex session requires user login or unavailable permissions, document that acceptance gate as unverified, do not fake success.
- [ ] **Step 4:** Run `uv run ruff check .`, `uv run pytest -q`, `docker compose config --quiet` and the authenticated image smoke. Expected: all available automated tests pass, all 24 synthetic queries meet their expected sets, and no skipped infrastructure tests. Record commands, counts, versions and limitations in `docs/validation.md`. Live acceptance remains explicitly pending until authorized account access: actual schemas/windows, field authority and ValuePack formula, native attribute feeds, catalog sizes and real query relevance. Fixture-complete is not production-verified.
- [ ] **Step 5:** Commit: `git commit -m "test: verify catalog resilience and Codex workflows"`.

## Self-review and handoff

Coverage mapping: source scope/authority Tasks 1–4; atomic imports and outages Task 5; matching/price semantics Task 6; exhaustive filtering and pagination Task 7; discovery/outbox Task 8; MCP/auth Task 9; skills/deployment Tasks 10–11. Review Focus cases have named owning tests. Interfaces share the vocabulary above; final names must match in generated schemas and skills. No supplier credentials, tunnel setup or live write operation is required by this plan.

Before execution, review this plan with the user. Preserve the selected inline execution method. At execution, use the executing-plans ledger and worktree process, then one fresh whole-branch reviewer with this spec, plan, Review Focus and ledger rulings. Do not ask the user to select an execution method again. Do not push or merge as part of plan completion.
