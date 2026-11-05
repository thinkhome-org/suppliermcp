# Live Supplier Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate complete available product data from the user's eD PUBLIC and 100MEGA accounts and prove it works through the local authenticated MCP.

**Architecture:** Extend the existing adapters, artifact store and PostgreSQL publication path. Track contributions by endpoint, preserve native data, and project only verified semantics into search and comparisons. Keep Typesense disposable and the seven MCP tool names compatible.

**Tech Stack:** Existing Python/uv, httpx, defusedxml, psycopg/PostgreSQL, Procrastinate, Typesense, FastMCP and Docker; no additional service.

**Spec:** `docs/superpowers/specs/2026-11-05-live-supplier-data-design.md` (approved by user: “vse schvaluji”).

## Global Constraints

- Supplier access remains read-only.
- Orders, invoices, claims, customer records, account administration and writes remain excluded.
- eD PRIVATE remains optional and disabled; no authenticated validation without access.
- No manufacturer-site enrichment, procurement optimization or public tunnel is added.
- Keep PostgreSQL authoritative, Typesense rebuildable, existing MCP tools and English repository content.
- Raw captures and secrets stay outside Git.
- Restricted exports are not called outside their windows.
- No silent truncation; no guessed prices, freshness, units or packaging semantics.
- Native execution remains the user's previously selected method; one independent whole-branch review at the end.

## Review Focus

1. Midstream disconnect or malformed final record must not publish a partial catalog (Tasks 1, 2, 4).
2. An empty valid enrichment snapshot must remove its own old facts without deleting other sources (Task 2).
3. Different endpoint windows and unknown timezones must not cause prohibited polling or retry storms (Tasks 3, 7).
4. Multi-valued facts and conflicting single-value observations must remain distinguishable in filters and details (Tasks 2, 5).
5. A very large individual description and a 100,000-row listing must remain reachable without oversized responses or memory-proportional full-detail materialization (Task 6).

## Files and responsibilities

- Existing `suppliers/transport.py`, `sync/artifacts.py`: validated streaming and retained evidence.
- Existing `suppliers/ed/public.py`, `ed/gateway.py`, `mega/adapter.py`, `mega/capabilities.py`: supplier protocol and semantics.
- New `suppliers/mega/exports.py`: explicit verified product-export contracts and record normalization; no generic arbitrary URL access.
- Existing `catalog/contracts.py`, `catalog/repository.py`, `sync/publish.py`, `sync/jobs.py`: endpoint-scoped persistence, ordering and coverage.
- New `migrations/005_endpoint_contributions.sql`: endpoint ownership and multi-valued facts; preserve existing rows.
- Existing `search/schema.py`, `search/listing.py`, `search/index.py`, `search/exact.py`: queryable native data and compact immutable result snapshots.
- New `mcp/details.py`, `migrations/006_detail_snapshots.sql`: principal-bound stable detail continuation; existing `mcp/tools.py` exposes optional parameters.
- Existing `config.py`, `worker.py`, Compose files, skills, Codex integration docs: runtime activation and operation.
- New `scripts/live_verify.py`: opt-in read-only verification using environment credentials, sanitized reports only.
- New `tests/test_live_contracts.py`, `tests/integration/test_endpoint_contributions.py`, `tests/integration/test_complete_product_data.py`: regressions from live discoveries with synthetic fixtures.
- Existing `docs/supplier-api/` inventory and `docs/validation.md`: per-endpoint evidence and final acceptance results.

### Task 1: Stream and validate eD catalog downloads

**Files:** Modify `suppliers/transport.py`, `sync/artifacts.py`, `suppliers/ed/public.py`, `suppliers/ed/gateway.py`, `config.py`; test `tests/test_transport.py`, `tests/test_artifacts.py`, `tests/test_live_contracts.py` (all source paths relative to `src/suppliermcp/`).

**Interfaces:** Preserve `SupplierTransport.read(...) -> bytes` for small SOAP responses. Add `SupplierTransport.download(url: str, store: ArtifactStore, manifest: BatchManifest) -> Path` with identical destination validation and a fresh artifact on each retry. Preserve `EdPublicAdapter.fetch(domain, codes=None) -> BatchManifest` and `parse(manifest) -> Iterator[ParsedRecord]`.

- [ ] Write tests `test_ed_lowercase_export_status` (lowercase URL is downloaded), `test_ed_not_ready_is_polled` (no status-envelope import), `test_ed_status_without_catalog_is_rejected` (`invalid_export`), `test_partial_download_is_not_retained_as_complete` (no active partial artifact), and `test_streaming_limit_rejects_last_chunk` (`payload_too_large`, no publication). Reuse existing HTTP mocks; never use live credentials in tests.
- [ ] Run `uv run pytest tests/test_live_contracts.py tests/test_transport.py tests/test_artifacts.py -q`; verify the new cases fail for the documented defects.
- [ ] Implement streaming into `ArtifactStore.save`, restart the complete transfer after retryable stream failures, preserve TLS/DNS/redirect/auth restrictions and enforce encoded/expanded budgets. Accept the exact known eD status spellings. Prefer documented ZIP for the canonical full PUBLIC import, retaining XML support and existing test fixtures. Validate actual product roots before accepting an empty import. Release processed XML nodes.
- [ ] Run the same tests; expected all pass. Parse the already captured 619,833,546-byte PUBLIC XML without another supplier request and reconcile 124,532 items/offers. Measure memory and bytes; configure sufficient account limits with explicit headroom rather than removing bounds.
- [ ] Commit the task with `fix: stream and validate live eD catalog exports`.

### Task 2: Preserve endpoint contributions and multi-valued facts

**Files:** Modify `catalog/contracts.py`, `sync/publish.py`, `sync/artifacts.py`, `catalog/repository.py`; create migration 005 and `tests/integration/test_endpoint_contributions.py`.

**Interfaces:** Add optional `Observation.value_key: str = ''` and `Observation.cardinality: Literal['one','many'] = 'one'`; existing inputs remain valid. Add `BatchManifest.authoritative_identity: bool = False` and `replace_scope: Literal['none','items','endpoint'] = 'none'`. Keep `stage(conn, manifest, rows) -> UUID` and `publish(conn, run_id, *, accept_reason=None) -> int`. Existing adapters explicitly declare baseline identity authority. Endpoint ownership is `(interface, endpoint)`; no external API changes.

- [ ] Add tests for independent endpoint checkpoints, out-of-order publications, unchanged evidence age, empty replacement removing only its endpoint, targeted replacement touching only requested items, multiple values for one native parameter, same-field conflict across authoritative sources, and migration of existing rows without loss. Assert failed final parsing leaves the previous revision and zero published new rows.
- [ ] Run `uv run pytest tests/integration/test_endpoint_contributions.py -q`; expected new behavior fails.
- [ ] Extend checkpoint/offer/schema/relationship ownership with endpoint columns. Backfill existing ownership from stored observations/manifests where provable, otherwise use a documented legacy owner. Observation primary keys include `value_key`; relationships retain source and endpoint. Preserve domain-level compatibility summaries for existing callers. Replace only a successful declared scope, never on failed parsing; no enrichment-driven identity retirement. Retain newest successful evidence per endpoint in artifact pruning.
- [ ] Stream staging with psycopg COPY and publication with bounded batches/server cursors instead of `fetchall()` of the whole catalog. Avoid duplicating observations in identity/offer JSON when their authoritative table already stores them; hydrate existing public return types from the table. Refresh filters/index once per changed item. Preserve atomic publication and quarantine behavior.
- [ ] Run `uv run pytest tests/integration/test_endpoint_contributions.py tests/integration/test_sync.py tests/integration/test_offer_refresh.py tests/integration/test_review_regressions.py -q`; expected all pass, including legacy cases.
- [ ] Commit with `feat: preserve endpoint-scoped catalog contributions`.

### Task 3: Verify 100MEGA contracts and normalize all product exports

**Files:** Modify `suppliers/mega/adapter.py`, `suppliers/mega/capabilities.py`, `suppliers/offer_contract.py`; create `suppliers/mega/exports.py`; extend `tests/test_mega.py`, `tests/test_live_contracts.py`, `docs/supplier-api/`.

**Interfaces:** Add `parse_capabilities(data: bytes) -> dict` to capabilities.py, fail closed on unexpected table structure. Extend `require_window(contract, mode, now=None)` to use per-mode day/hour windows. Add `MegaAdapter.fetch_export(endpoint: str, *, codes: list[str] | None = None, from_time=None, to_time=None) -> BatchManifest`; the existing domain `fetch` delegates to verified canonical exports. Add `normalize_export(manifest, contract) -> Iterator[ParsedRecord]` in exports.py.

- [ ] Add tests for the captured table's distinct full/targeted hours, disabled modes, absent timezone, malformed capabilities, PriceOrd versus PriceDea, root CurCode, Row/StiId parameter joins, omitted fees remaining unknown, multiple EANs, nested packaging and relationship direction. Assert non-product export names cannot be fetched through this adapter.
- [ ] Run `uv run pytest tests/test_mega.py tests/test_live_contracts.py -q`; expected new cases fail.
- [ ] Implement explicit product export dispatch. Consume the committed inventory as documentation, not unconditional permission. Preserve root metadata and all nested/scalar fields; use source IDs, field paths and stable child keys. Group Row parameters by product without erasing baseline identity. Normalize known product relationships into SchemaRecord, retain unproven structures as typed source-scoped evidence. Implement `_El` equivalence without duplicate ingestion. Unknown special exports remain visible unverified entries until schema/sample joins prove them.
- [ ] Correct prices using export-specific verified price fields and root currency. Derive links only from supplier-declared bases, without fetching external pages. Preserve source-generation versus price evidence times. Represent multiple values with Task 2 cardinality and stable keys; never reinterpret QtyPack as order_multiple.
- [ ] Run focused tests; expected all pass. Probe each in-scope unique export only in its permitted mode/window and update inventory evidence; verify special export equivalence or unique contributions explicitly. A failed/empty export is recorded with its actual state, not claimed as integrated.
- [ ] Commit with `feat: normalize verified 100MEGA product exports`.

### Task 4: Ingest complete product enrichment with independent coverage

**Files:** Modify `sync/jobs.py`, `suppliers/ed/public.py`, `suppliers/ed/private.py`, `catalog/repository.py`, `worker.py`; test `tests/integration/test_jobs.py`, `tests/integration/test_endpoint_contributions.py`.

**Interfaces:** Add `run_export_refresh(conn, adapter, endpoint: str, codes=None) -> int`; keep `run_refresh(conn, adapter, domain, codes=None)` compatible. `source_state.data.endpoints[endpoint]` records outcome, attempted_at, last_success_at, next_allowed_at and verified coverage. Add maintenance CLI `refresh INTERFACE --domain DOMAIN` and `refresh INTERFACE --endpoint ENDPOINT`; never expose arbitrary supplier writes.

- [ ] Add tests asserting one failing enrichment leaves baseline and other endpoint values usable, successful stock does not claim complete categories, missing PRIVATE remains disabled, empty valid enrichment clears its old values, unknown modes are not scheduled, and a night-only export has a next-eligible time rather than a minute retry loop.
- [ ] Run `uv run pytest tests/integration/test_jobs.py tests/integration/test_endpoint_contributions.py -q`; expected new cases fail.
- [ ] Orchestrate baseline plus verified unique enrichment, each with Task 2 endpoint ownership and Task 3 contracts. Canonical eD PUBLIC ingestion covers all 28 observed fields and commodities; derive only supplied classification, not PRIVATE navigator data. Track equivalent product encodings in the inventory, not duplicate jobs. Keep PRIVATE adaptation tests green without making authenticated PRIVATE calls.
- [ ] Schedule each endpoint inside its allowed window with supplier serialization. Use explicit configured intervals, no guessed supplier rate permission. Report unavailable, restricted, not_fetched, partial and successful states separately; retain older data on failures. Refresh requests return meaningful pending/unavailable status for PUBLIC's full-only API.
- [ ] Run task tests plus `tests/integration/test_resilience.py`; expected all pass. Commit with `feat: refresh product enrichment with endpoint coverage`.

### Task 5: Make complete native product data searchable and filterable

**Files:** Modify `search/schema.py`, `search/listing.py`, `search/index.py`, `search/exact.py`, `catalog/mappings.json`; create `tests/integration/test_complete_product_data.py`.

**Interfaces:** Preserve `catalog_schema(conn, category=None)`, `validate_filter(f, schema)`, `refresh_values(conn, item_ids)`, `matching_ids(conn, query)`, `document(row, conn=None)` and `lookup(conn, identifiers)`. Extend schema metadata with source names, labels, cardinality, units when verified and category membership. Keep source-scoped native names and existing common fields compatible.

- [ ] Add tests for two valid parameter values matching either eq/in choice, an absent parameter returning unknown, conflicting single-value facts staying unresolved, category membership from a tree dictionary, alternate EAN lookup preserving zeros, and discovery matching a supplied parameter/relationship label. Assert unknown units cannot activate numeric mappings.
- [ ] Run `uv run pytest tests/integration/test_complete_product_data.py -q`; expected new cases fail.
- [ ] Store multiple catalog values using stable value keys and SQL EXISTS/bool aggregation with existing three-valued query behavior. Join dictionaries to readable names without replacing native codes. Keep arbitrary nested metadata discoverable through details; index meaningful supplier text rather than XML syntax. Extend exact lookup to verified alternate identifiers. Populate common mappings only where definitions and units are verified in supplier evidence; record evidence links in inventory.
- [ ] Use bounded bulk refresh/index projections to avoid per-fact round trips at live scale. Run `uv run pytest tests/integration/test_complete_product_data.py tests/integration/test_search.py tests/integration/test_listing.py tests/test_filters.py tests/test_matching.py -q`; expected all pass.
- [ ] Commit with `feat: search complete native supplier product data`.

### Task 6: Bound result snapshots and paginate every large product detail

**Files:** Modify `catalog/contracts.py`, `search/listing.py`, `search/exact.py`, `search/discovery.py`, `mcp/tools.py`; create `mcp/details.py`, migration 006; extend `tests/integration/test_mcp.py` and `tests/integration/test_complete_product_data.py`.

**Interfaces:** Add `ProductView.detail_continuation` metadata while preserving current fields. Expose `get_product(product_id: str | None = None, section: str | None = None, cursor: str | None = None)` with sections `overview`, `observations`, `attachments`, `relationships`. Add `product_page(conn, product_id, section, cursor, principal, settings) -> ProductView | dict` in details.py. Cursors alone continue immutable snapshots; mixed changed arguments fail. Use existing 30-minute lifetime and principal checks.

- [ ] Add tests for oversized descriptions split into ordered text chunks, every original byte reachable after pagination, duplicate-free multi-page relationships, expired/wrong-principal cursors, import changes between pages, and a large listing materializing compact summaries rather than full observation bodies. Assert old get_product calls still succeed with compatible core identity/offer fields.
- [ ] Run `uv run pytest tests/integration/test_mcp.py tests/integration/test_complete_product_data.py -q`; expected new cases fail.
- [ ] Build compact listing/search/exact views with explicit detail availability; retain full evidence in authoritative storage. Replace the giant JSON results array with row-based immutable compact snapshots using bounded insertion and page reads. Detail snapshots use bounded row/chunk storage, explicit section counts and next cursors. Response budgets account for the full serialized envelope; no unreachable oversized single value.
- [ ] Run tests plus existing cursor/persistence tests; expected all pass. Verify a 100,000-row synthetic compact listing without loading 100,000 full product bodies. Commit with `feat: paginate complete product evidence within MCP budgets`.

### Task 7: Activate persistent local Docker and Codex access

**Files:** Modify `config.py`, `compose.yaml`, `.env.example`, `docs/operations.md`, `integrations/codex/README.md`, `skills/product-discovery/SKILL.md`, `skills/offer-comparison/SKILL.md`; extend `tests/test_packaging.py`, `tests/evaluation/test_workflows.py`.

**Interfaces:** Continue Settings.from_env and source_contracts_path. Document protected local runtime directory, read-only contract mounts and two enabled credential pairs. Existing edshop MCP configuration remains untouched. Use RS256 verifier and local HTTP URL; private signing key never mounted into server/worker.

- [ ] Add tests that Compose mounts contracts into both server and worker, plugin output contains no supplier secrets, skills teach schema-first filters and detail continuation, and optional credentials still support all eight interface combinations.
- [ ] Run `uv run pytest tests/test_packaging.py tests/evaluation/test_workflows.py tests/test_contracts.py -q`; expected new assertions fail where behavior is missing.
- [ ] Configure a dedicated persistent local Compose project using credentials from the supplied email and existing edshop environment file without printing values. Generate local signing material separately, configure authentication and provide usable Codex connection instructions. Add no public tunnel. Preserve existing services and volumes; check port availability before binding.
- [ ] Start database/search, migrate, start MCP/worker, and run permitted full imports. Use captured data only as labeled initial evidence; do not fake fresh supplier timestamps. Leave night-only jobs visibly pending until their actual allowed window. Record runtime paths and endpoint without secrets.
- [ ] Run task tests and restart the local project without deleting volumes; expected catalog and auth persist. Commit tracked runtime/docs changes with `feat: activate authenticated local supplier runtime`.

### Task 8: Prove live behavior, document limits and review

**Files:** Create `scripts/live_verify.py`; modify `scripts/codex_acceptance.py`, `docs/validation.md`, `docs/supplier-api/`, `docs/implementation-decisions.md`; extend `tests/evaluation/test_queries.py` and `tests/integration/test_resilience.py`.

**Interfaces:** `scripts/live_verify.py --report PATH` reads configured authenticated MCP and protected local source settings, performs only allowlisted product reads, and writes a sanitized JSON/Markdown evidence report. Supplier probes require an explicit `--probe-suppliers` flag and obey windows. No credentials, tokens, account URLs or private prices are reported.

- [ ] Add self-check tests for report redaction and endpoint classification, including a deliberately secret-bearing exception; assert no excluded method can be invoked. Add resilience tests for bad credentials/timeouts/one source disabled while retained data remains queryable, plus missing/rebuilt Typesense.
- [ ] Run the focused tests and watch new requirements fail; implement the minimal verifier using existing MCP client/acceptance patterns and supplier adapters.
- [ ] Reconcile download/parse/publish/index/query counts for actual available catalogs and enrichment. Validate known captured SKU/EAN/MPN, Czech/English terms, category/parameter filters, leading-zero IDs, detail/list continuation and quantity comparisons. Verify prices against protected captures without placing commercial values in reports. Test real Codex tool-only and built-in-skill workflows.
- [ ] Run `uv run pytest -q`, `uv run ruff check .`, Docker build and authenticated restart/persistence checks; expected all pass with no unexplained skips. Measure actual import duration, memory and query latency; investigate failures before declaring completion.
- [ ] Finish per-endpoint evidence statuses including every failed/unavailable/scheduled export. Respect night-only restrictions; a required missing live test remains an explicit incomplete acceptance item, never a simulated pass. Persist reproducible commands for remaining external blockers.
- [ ] Commit with `test: verify live supplier ingestion and MCP workflows`. Dispatch the one final independent reviewer under executing-plans, fix Important/Critical findings with failing-then-passing regressions, rerun the suite, and finish the branch using preserved user authorization. Report actual completion and all remaining supplier-side limits.

## Self-review

All spec sections map to tasks: inventory/semantics (3, 4, 8), transport/size (1), durability/authority/replacement (2), search/filtering (5), complete detail reachability (6), local activation and outage behavior (7, 8). Each Review Focus case has an owning test. Existing public function signatures remain compatible except optional additions. Changes to persisted keys require non-destructive migrations and legacy tests. Live external failures are evidence gaps, not permission to invent data or bypass restrictions.
