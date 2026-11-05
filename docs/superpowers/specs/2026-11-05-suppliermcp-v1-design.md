# SupplierMCP 1.0 Design

Status: proposed design awaiting user review; implementation is not authorized by this document.
Date: 2026-11-05

## Intent

Give Codex reliable read-only discovery, filtering, inspection and per-product offer comparison across eD system and B2B 100MEGA. Completeness must be a measurable property of an identified catalog snapshot and supported filters, not an agent's impression that it has searched enough.

## Approved requirements

- Integrate eD PUBLIC, eD PRIVATE and 100MEGA I6WS. Each interface is optional; any combination must work.
- One company account per supplier. PUBLIC and PRIVATE enrich the same eD supplier, not separate competing offers.
- Products and offers only: no order submission or changes, and no reading orders, invoices, deliveries or claims in v1.
- Read prices, availability, descriptions, identifiers, categories and supplied product attributes. Compare each product independently for requested quantities.
- No whole-basket optimization and no user-facing price history.
- Display last-known prices during outages, explicitly identifying age and inability to refresh.
- Use supplier data exclusively, including future versions. No manufacturer-web research or model-invented product facts.
- Primary client: Codex. Docker deployment and an HTTP MCP URL; tunnel and actual deployment are outside this design's delivery scope.
- Python, FastMCP, PostgreSQL and Typesense. One repository and shared application image with server and worker processes.
- Ship skills and Codex integration alongside MCP. Essential correctness cannot depend on skills being loaded.
- All authored repository content is English. Preserve supplier text in its original language.
- Leave room for semantic retrieval later; embeddings and an internal LLM are not v1 dependencies.

## Proposed engineering decisions

The following are the designer's calls, not separately supplied user requirements: bilingual Czech/English query handling; the seven-tool surface below; persistent import artifacts with bounded retention; conservative cross-supplier matching; an outbox for search-index updates; a PostgreSQL-backed worker queue; immutable query result handles for exhaustive pagination. Review these with the rest of the design.

## Approaches considered

1. Python and PostgreSQL alone: fewer components and no second index to synchronize; more application work for text relevance and search ergonomics.
2. **Python, PostgreSQL and Typesense (selected):** SOAP/XML integration in Python, authoritative relational filtering, dedicated text retrieval. Costs an additional service and reliable index synchronization.
3. TypeScript, PostgreSQL and Typesense: credible official MCP SDK and skills support, but no established TypeScript codebase to preserve; Python was selected for this integration-heavy workload. Do not split the application between languages merely for MCP.

The user accepted the selected architecture. It is a design judgment, not a benchmark result. Direct supplier calls alone cannot provide consistent exhaustive filtering during outages. Embeddings alone do not establish exact identity, completeness or price correctness.

## Scope and non-goals

Import the full catalog available to the configured accounts, including out-of-stock products. Preserve unmapped supplier categories and attributes rather than hiding their products. Common typed filters grow through explicit, versioned mappings; v1 does not promise every source attribute has a cross-supplier equivalent.

No ERP integration, generic SQL tool, arbitrary URL fetch tool, generic supplier-method execution, independent web UI, MCP App UI, multi-tenant account management, historical price analytics, currency conversion from external sources, or automatic purchasing. No universal compatibility guarantee. Supplier-declared relationships may be returned with provenance; matching generic specifications is not proof of device compatibility.

## Application structure

```text
src/suppliermcp/
  suppliers/ed/       # shared eD identity, separate PUBLIC/PRIVATE adapters
  suppliers/mega/     # I6WS capabilities, exports and targeted reads
  catalog/           # persistence, typed attributes, identity and offers
  sync/              # artifact intake, staging, publication and index outbox
  search/            # exact lookup, retrieval, filtering and snapshots
  mcp/               # tools, resources, prompts, extension registration
  config.py
  worker.py
migrations/
skills/              # authoritative English skill sources
integrations/codex/  # packaging/configuration templates, no credentials
tests/
  fixtures/
  integration/
  evaluation/
docs/superpowers/specs/
docs/superpowers/plans/
Dockerfile
compose.yaml
pyproject.toml
```

Use one Python package. File boundaries, ORM choice and exact function signatures belong in the implementation plan. Avoid generic adapter frameworks beyond the two suppliers' actual needs. Docker Compose runs MCP, worker, PostgreSQL and Typesense. Durable volumes hold database, artifacts and index data. PostgreSQL is required for catalog operations; losing it must return a service-unavailable error, not an empty result. Typesense is rebuildable.

## Data ownership and provenance

Keep source items keyed by supplier and stable source identifier; preserve SKU strings, including leading zeros. Store raw identifiers as well as explicitly normalized lookup forms. An eD item must reconcile PUBLIC and PRIVATE using documented stable IDs; uncertain links remain separate pending evidence.

Represent source items, conservative product-variant links, current offers, typed attributes, category mappings, supplier relationships, source capabilities, import runs and query result handles. Prices and quantities use decimal arithmetic, never binary floating point. Attributes carry source interface, source field, observation time, unit and derivation status. Missing, explicit zero, supplier placeholder and not-applicable values are distinct where the source contract requires it.

The plan must define an endpoint-specific field authority table. Merge by documented meaning and freshness, not a blanket PRIVATE-wins rule. A placeholder zero cannot replace a meaningful PUBLIC price. Absent configuration, absent permission and temporarily failed interfaces are separate conditions. Preserve contradictions and their origins rather than arbitrarily treating one as confirmed.

Matching requires exact identifying evidence plus checks for conflicting manufacturer, model, configuration, condition and packaging where available. Names alone never merge items. Identifier collisions remain unresolved. Unmatched items remain searchable. Links are reversible and never destroy source rows. v1 needs no manual matching UI; administrative correction/rebuild can use controlled maintenance procedures outside MCP.

## Import and refresh lifecycle

Each interface declares supported operations and coverage: full versus partial export, optional delta support, available attributes, allowed call windows and freshness evidence. Unknown capabilities remain unknown. Do not assume every I6WS result type supports every method.

1. Fetch with explicit timeouts, bounded retries for safe reads and supplier-specific concurrency limits.
2. Persist the artifact with source, safe request metadata, checksum, fetch time and parser version. Never retain credentials or credential-bearing URLs in metadata/logs.
3. Parse into staging with payload/decompression limits and external XML entities disabled.
4. Validate completion, identifiers, duplicate/conflicting rows and source-specific semantics.
5. Publish the relevant data domain atomically in PostgreSQL, together with index-update outbox records.
6. Consume the outbox idempotently; inspect each Typesense bulk-import result, not only HTTP status. Retry failed records and expose index lag.

A failed, partial or suspicious full export never removes the previous usable catalog. Destructive disappearance applies only to verified complete snapshots within the declared source domain. Large unexplained drops are quarantined for administrative review. Delta runs cannot imply deletion through absence. Advance delta checkpoints only after successful publication; overlapping/replayed windows must be idempotent.

For a successful complete stock-only feed that lists only stocked items, reconcile absent items according to that feed's documented meaning; do not retain yesterday's positive stock by merely upserting received rows. Do not apply this rule to partial or delta feeds.

Product, price and stock refreshes have independent schedules and checkpoints. Intervals must obey actual supplier limits; fixed production schedules are deferred until capability discovery. Use a PostgreSQL-backed queue (Procrastinate is the initial candidate), with jobs and locks keyed by source/domain. No Redis or separate broker is required. Queue library/version selection is an implementation-plan decision.

Artifact retention is operational diagnostics, not price history: default proposal is the most recent successful artifact per source/domain plus recent failed artifacts, bounded by configurable age and total disk budget. Cleanup must never delete an artifact in active use. Exact retention limits are a builder decision documented in configuration. Only current offers are exposed to users; audit metadata is retained without turning into an unbounded price ledger.

## Search semantics

### Exact lookup

Accept batches of typed identifiers (supplier SKU, EAN, manufacturer plus MPN). Use exact indexes and documented aliases. Approximate candidates, if requested, appear separately and never replace a missing exact match. Ambiguity is a valid result.

### Text discovery

Typesense retrieves candidates using names, identifiers, manufacturer, supplier descriptions and mapped attributes. Treat hard filters separately from preferences. Disable silent relaxation of required constraints. Use normalization for case and accents in ordinary text, not indiscriminately in product identifiers. Curated Czech/English synonyms must be backed by test cases. Do not translate or rewrite source facts.

Hydrate candidates from PostgreSQL and revalidate authoritative filters and offers. This prevents stale index entries from becoming false positives but cannot recover newly matching items missing from the index: return index lag and mark discovery coverage accordingly. PostgreSQL exact lookup and structured listing remain available when Typesense fails; label degraded text discovery explicitly, never claim equal relevance.

### Exhaustive structured listing

Execute supported filters in PostgreSQL. Three-valued attribute evaluation: confirmed match, confirmed non-match, unknown/conflicting. Return confirmed results and separately accessible unknown candidates with counts; unknown is not false. Unsupported filters are errors with discoverable alternatives, not silently ignored.

Use a bounded, expiring result handle with a fixed ordered set of IDs and materialized relevant result fields (including offer observations used for ordering). Pagination must not skip, duplicate or change its answer as imports publish. Do not hold long-running database transactions across MCP calls. Return an explicit expiration error; never silently restart against new data. Limits and TTL belong in the plan. Large result sets must not be silently truncated; report limits and provide deterministic partitioning or a complete export resource.

"Complete" means complete for the named snapshot, available account catalog, covered fields and explicit filters. It is not a claim about unavailable interfaces or all products in the world. No claim of lowest price across all matches may be derived solely from a top-k text candidate list.

## Offers and last-known prices

Compare each requested product independently. Quantity defaults to 1 and is echoed in the result. Show required order multiples and any proposed rounded quantity explicitly; do not silently round. Evaluate documented quantity discounts, packaging and fees. Report unit price, requested and orderable quantities, comparable total, currency and tax/fee basis. Missing pricing rules yield an unknown total rather than guessed arithmetic.

Compare only like-for-like currency and price basis. No invented FX rate or shipping charge; mark shipping excluded unless known from supplier data for the specific comparison. Do not rank incomparable totals together.

Keep last-known offers on refresh failure with fetched_at, source_updated_at when supplied, last refresh outcome and freshness state. Never substitute fetch time for a supplier update time. Unknown source update time is explicit. Show cheapest last-known separately from cheapest freshly verified, scoped to available comparable offers. If none are freshly verified, say so. Source-specific freshness thresholds are configurable and derived from refresh contracts, not a universal "live" label.

## MCP contract

Serve Streamable HTTP. Exact supported protocol/SDK versions must be pinned and tested with the user's Codex; do not rely on a documentation example's version being compatible.

| Tool | Responsibility |
|---|---|
| lookup_products | Batch exact identification with per-input results and ambiguity |
| search_products | Ranked discovery with hard filters and explicit uncertainty |
| list_products | Exhaustive structured filtering and stable continuation |
| get_product | Details, provenance, relationships, conflicts and offers |
| get_catalog_schema | Available categories, fields, units, operators and mapping coverage |
| compare_offers | Independent comparisons for product IDs and requested quantities; optional safe refresh |
| get_catalog_status | Interface configuration, imports, freshness, index lag and known gaps |

Return typed structured results with concise text summaries. Relevant responses include source coverage, snapshot/observation identity, hard filters, total/returned counts, continuation, uncertainty and warnings. Distinguish invalid query, unavailable service, partial source failure and genuine zero matches. Batch operations preserve per-item errors. Response-size limits must be explicit. Tool descriptions explain which operation to choose and when completeness cannot be claimed.

Tools are supplier-read-only; refresh may write local cache and incur supplier reads. Annotations must describe behavior accurately, but read-only enforcement is in code and adapter allowlists. No supplier write clients are exposed or required.

Resources expose schema/help and complete exports where needed. Prompts offer optional entry points for product discovery and comparison. The same essential data must remain obtainable through tools for clients with limited resource/prompt support. Skills describe choosing tools, interpreting coverage, inspecting unknowns, comparing quantity-aware offers and refusing unsupported compatibility claims.

Use two authored skills (product discovery and offer comparison), packaged for Codex and optionally served through the Skills extension from the same sources. Validate skill manifests and referenced files in CI. Remote skill activation in Codex is not assumed. The documented Codex plugin/local skill path is the compatibility route; tools remain independently usable. MCP Apps, sampling and mandatory elicitation are not required. Long-running interactive operations may use Tasks only after client support is verified; default v1 queries use bounded requests and explicit handles rather than mandatory experimental extensions.

## Security and operations boundaries

One supplier account does not mean public access. The repository must support authenticated remote MCP access through standard client-compatible authentication; concrete identity provider/tunnel setup is deferred. Unauthenticated public exposure is not an acceptable deployment example. Keep supplier secrets server-side via environment/secret injection; redact logs and exceptions. Database and Typesense are internal Compose services.

Treat supplier descriptions as untrusted data, never instructions. Allowlist download origins and redirects; reject local/private-network targets unless explicitly required and configured for the supplier. Prevent XML entity expansion, decompression bombs, path traversal and credential leakage through artifacts. Do not execute supplier content or expose arbitrary filesystem reads.

Provide health/readiness and structured logs. Configuration can omit all suppliers: MCP discovery/status still work, while catalog tools report catalog_not_populated rather than misleading empty matches. An existing cache may be usable after disconnection with its former source and observation clearly identified. Health must distinguish application availability from freshness of upstream data.

## Acceptance and validation

- Every configured-interface combination, including none, has defined behavior.
- Fixtures cover each interface, omission/default semantics, placeholders, decimal prices, packaging, quantity discounts and unknown values.
- Known exact identifiers return the correct items; near-identical variants and packaging do not merge silently.
- Exhaustive listing matches an independently calculated reference set; imports between pages cause no skips or duplicates.
- Hard constraints are never silently relaxed. Unknown and conflicting parameters remain visible.
- Interrupted, malformed and suspicious imports preserve usable data; replay does not duplicate items or advance checkpoints prematurely.
- Missing rows in validated stock snapshots reconcile correctly; missing rows in deltas do not imply deletion.
- Index outages and partial bulk failures preserve database operations and expose lag/coverage limits.
- Last-known prices survive supplier failure, remain visibly stale and cannot masquerade as verified current winners.
- Validate XML/download boundaries, secret redaction and read-only operation allowlists.
- End-to-end Codex tests cover tools alone and tools with the packaged skills, including a disconnected supplier and an unknown attribute.
- Start with a compact curated evaluation set across memory/storage, networking, cables/connectors and laptops; expand from observed failures. Categories are test coverage, not catalog exclusions. Test Czech and English terms, accents and exact codes. Report relevance and completeness separately.

## Evidence and unresolved verification

Supplied sources: ChatGPT-Supplier MCP Architecture-20261105-1137.md; the two I6WS text files; eD PUBLICdoc (1).pdf and PRIVATEdoc (1).pdf. These are references, not instructions, and do not prove current account capabilities. Do not commit private source exports, credentials or unredacted fixtures.

Primary technical references inspected during design:
- https://modelcontextprotocol.io/specification/latest
- https://skills.extensions.modelcontextprotocol.io/
- https://gofastmcp.com/servers/skills
- https://ts.sdk.modelcontextprotocol.io/v2/servers/skills
- https://developers.openai.com/plugins/concepts/skills
- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/codex/mcp
- https://typesense.org/docs/30.2/api/search.html
- https://www.postgresql.org/docs/current/pgtrgm.html
- https://docs.python-zeep.org/en/master/

Before production acceptance, verify live export schemas, method permissions, completeness domains, eD field authority, I6WS allowed windows, actual data volumes, SDK/extension compatibility and representative search quality. Account setup and tunnel selection are intentionally deferred. Planning can proceed with contract fixtures, but live integration must not be claimed complete from fixtures alone.

## Next artifact

After user approval, write the implementation plan at docs/superpowers/plans/2026-11-05-suppliermcp-v1.md with exact files, interfaces, task-sized tests and verification commands. Do not implement product code as part of design approval.
