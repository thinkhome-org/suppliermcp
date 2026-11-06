# Validation evidence

For v2, see the [candidate acceptance and outstanding cases](supplier-api/v2-acceptance.md), [per-operation results](supplier-api/v2-read-probes.json) and [catalog search validation](supplier-api/v2-search-validation.md). The dated results below describe the original v1 deployment.

## Live acceptance on 2026-11-05

The protected local project is `suppliermcp-live`, with authenticated MCP at `http://127.0.0.1:8000/mcp`. Machine-readable, payload-free evidence is in [live-validation-2026-11-05.json](live-validation-2026-11-05.json). The first snapshot below precedes the night-window follow-up. Counts are measured snapshots, not a promise that a changing supplier catalog is constant.

- **eD PUBLIC:** the documented ZIP was downloaded and all **124,532 products** were parsed, published, indexed and enumerated through MCP. The previously measured ZIP was 47,069,717 bytes, expanded XML 619,833,546 bytes. PUBLIC exposes 28 product fields; PRIVATE-only data is not invented.
- **100MEGA:** the full permitted stock export published **33,432 products**. A permitted targeted read of one real SKU additionally published `StoItemPriceOrdCur`, `CpsStiVal`, `StoItemEAN`, `StiPacking`, `StiRelation` and `AttSti`; that product had a price/currency, 727 observations and 16 directed relationships. Those targeted checks alone do **not** establish full baseline/price/parameter coverage. The initial snapshot preceded the verified night window, starting **21:00 Europe/Prague**; later full-export results are recorded below.
- **Reconciliation:** 157,964 active database products and 157,964 index documents; database/index revisions both 9 after the targeted updates were drained. Restarting PostgreSQL, Typesense and MCP retained all 157,964 products and authentication. Typesense needed time to reopen its index after restart; exact/list/detail calls remained independent of it and the queued index update succeeded on retry.
- **Live data checks:** sampled source artifact identifiers, eD price/currency and stock agreed with the published records without exposing commercial values. Actual MCP calls preserved a leading-zero EAN, did not conflate its zero-stripped spelling, resolved manufacturer+MPN, and matched both native text and numeric parameters. The latter reported the other 157,963 products as unknown, not as known nonmatches.
- **MCP checks:** unauthenticated requests returned 401; authenticated clients saw seven tools and two canonical skill resources. Schema discovery, exact lookup, list continuation, detail continuation, text search and quantity comparisons succeeded for both available sources. An unrestricted eD listing exceeded the deliberate 100,000-row snapshot limit and returned usable non-overlapping partitions. Following the first partition produced an immutable 100,000-row snapshot; the first-page materialization took 11.592 seconds, versus 3.724 seconds for the 33,432-product 100MEGA snapshot. These are local measurements, not a latency guarantee.
- **Actual Codex:** both installed-CLI sessions exited 0, using an isolated configuration without editing the existing edshop server. One used tools only; the other read the canonical project skills. Traces verified real tool calls, partition following, exact lookup, observation continuation, quantity 2 comparisons, and Czech `paměť` / English `memory` searches. Both described partial coverage and last-known prices rather than claiming a fresh winner. Protected traces remain outside Git.

## Night-window follow-up

After the permitted window opened, the full `StoItemBase` response downloaded and parsed successfully: **178,135,560 bytes**, **33,427 products/offers**, **281.02 seconds**, parser peak RSS **62,799,872 bytes**. Its authoritative publication completed in **731.45 seconds**, peak RSS **301,904 KiB**, at revision **18**. Five products from the earlier stock snapshot were no longer present in the complete baseline and were deactivated. The full `StoItemPriceOrdCur` export had already published at revision **17**. These are separate fetches from a changing catalog, not an atomic supplier snapshot.

The baseline initially failed three times before response headers at about 30 seconds. Streaming downloads now have a bounded 300-second read timeout (10-second connect), while small calls retain their shorter timeout. Every actual retry still revalidates the supplier window.

Live native dictionary requests reported totals of **231** category chunks and **5,117** presentation-tree chunks; first-page and continuation requests succeeded. This checks access and pagination, not every individual dictionary value.

The full `CpsStiVal` capture contained **151,305,572 bytes** and parsed into **1,397,248 normalized SchemaRecords** in **99.19 seconds**. Staging took **183.75 seconds**. Publication completed at revision **19** in **1,751.65 seconds**, including its wait behind the baseline publication; peak importer RSS was **646,252 KiB**. It published **9,501,202 observations** over **33,432 supplier product IDs**, including retained evidence for IDs no longer active in the later baseline. Actual MCP text and numeric native filters both matched a product against its newly published source values. This first full parameter import is expensive, and queued refresh/index work waits for the serialized publication lane.

The final authenticated MCP pass at **22:48 Europe/Prague** verified **157,959 active products and index documents**, with both revisions **19**. All seven tools passed their exercised workflows for both sources, including nonempty fulltext results, exact lookup, detail/list continuation and comparisons. First-page snapshot materialization took **17.138 seconds** for the 100,000-row eD partition and **7.071 seconds** for all 33,427 active 100MEGA products under concurrent background ingestion. These list times materialize the complete immutable result, not just the displayed page.

The worker remains running. At this snapshot, full EAN publication was in progress; full attachments, `CpsSti`, EPREL/GPSR, hooks/nodes, active/list exports, delivery terms, extended stock and selected X-family enrichment remained queued. Full attachments were explicitly queued so the earlier targeted check does not postpone their initial full refresh. Config/SIV and equivalent representations retain their separate endpoint/window statuses. These pending exports are **not** claimed as completed live acceptance; exact states and queued endpoints are included in the JSON evidence and API inventory.

## Performance and live fixes

The first PUBLIC publication exposed PostgreSQL's B-tree key-size limit on long descriptions. An incompressible-text regression reproduced it; migration 008 indexes a fixed-width digest while preserving the full value and checking original equality. The retained staged export was then published successfully without another supplier download or a fabricated fresh timestamp.

That publication took **595.01 seconds**, with importer peak RSS **130,828 KiB**. The complete index rebuild took **190.73 seconds**, peak RSS **144,728 KiB**. Publication and index rebuild intentionally serialize; rebuild delays new publications, while retained catalog queries remain available. This is a measured local account run, not broad capacity certification. Long-running jobs can delay the single worker's queue; monitor endpoint status and revisions.

Compact immutable snapshots avoid storing full descriptions in listings. Product evidence is paginated by section; oversized records use lossless ordered JSON chunks. Large schema responses use `_continuation`. Regression tests cover exact Unicode reconstruction, expiry/principal checks, import changes between pages, duplicate-free relationships and a 100,000-row compact listing.

## Automated verification

The final suite passes **145 tests**, no skips; `ruff check` passes. It includes real PostgreSQL and Typesense, all eight optional-interface configuration combinations, corrupt/interrupted imports, endpoint-scoped replacement, native multi-value filters, ambiguous identity rejection, stale prices after credential/timeouts, source isolation, index outage/rebuild, response budgets and authenticated HTTP.

```sh
uv run pytest -q
uv run ruff check .
docker compose --project-name suppliermcp-live --env-file /Users/samuel/.local/share/suppliermcp-live/runtime.env build
```

With the protected client token loaded into `SUPPLIERMCP_TOKEN`:

```sh
uv run python scripts/live_verify.py --report /protected/path/live-report.json
uv run python scripts/codex_acceptance.py --live --output /protected/path/codex-traces
```

`live_verify.py` does not call suppliers unless `--probe-suppliers` is explicitly supplied. Such probes use the existing product-only adapters and obey verified windows. Reports omit exception messages, credentials, identifiers and prices. Raw Codex traces can contain commercial product data and must remain protected.

## Explicitly incomplete acceptance

Full 100MEGA baseline, price and parameter exports were subsequently published in the permitted night window. Remaining enrichment/export variants' database acceptance and boundary-hour behavior are not universally verified. The inventory separately records 94 schema requests, 96 attempted product probes and 81 successful captured-response parser replays; a parser replay is not an integration pass. Only canonical representations are automatically scheduled. PUBLIC alternate transforms/direct-list encodings are mapped but not all exercised. No authenticated eD PRIVATE request was made.

Supplier price-update timestamps/freshness, every physical unit/packaging mapping, and ValuePack semantics are not universally established. Unknown data stays unknown; comparisons do not invent order multiples, fresh winners or comparable variants. Text search is discovery, capped at 1,000 candidates; use partitioned exhaustive listing for all retained matches. Cross-supplier equivalence/recall is not certified by the sampled tests.

No public tunnel, backup restore drill or native GUI plugin installation was performed. The local connection profile is prepared; actual Codex CLI access was verified. Database failure makes authoritative catalog tools unavailable. Old Typesense collections still require administrative cleanup after successful rebuilds.

The original v1 independent review had one deferred Minor: discovery against an existing empty index returns an empty non-exhaustive result rather than `catalog_not_populated`. Exact lookup/listing already expose that state. The separate final independent review found six Important issues, all fixed with failing-then-passing regressions: retry-window revalidation, empty targeted replacement, scalar/many conflicts, unchanged-success recovery flags, removed dictionary reindexing, and native dictionary/tree pagination. No Critical or new Minor issues remained in that review.
