# Validation evidence

Implementation tested locally on 2026-11-05. This is synthetic/local acceptance, not production supplier certification.

## Executed checks

- Unit and real PostgreSQL/Typesense integration tests, including three-valued filtering, immutable pagination, 100,001-row rejection/partitions, output budgets, quarantine, interrupted imports, cached-price outages, stock/price isolation, tied timestamp conflicts, exact identifiers and authenticated HTTP.
- 24 synthetic discovery queries across memory/storage, networking, cables/connectors and laptops, with 12 Czech/English pairs, must-find IDs and near-match exclusions. Every curated code resolves exactly. This establishes fixture behavior, not real-catalog recall.
- Docker build from pinned multi-platform digests; non-root application. Disposable Compose smoke verifies migration, seven tools, authenticated skill resources, all eight optional-interface startup combinations, and catalog persistence after database/server restart. Only the random smoke project's volumes are removed.
- Installed Codex CLI, `--ignore-user-config --ephemeral --sandbox read-only`, temporary working directory and environment bearer token. Both tool-only and canonical project-skill-assisted sessions exited 0. Actual tool traces were inspected: SKU `0007` retained zeros and resolved; `paměť DDR5` returned the seeded memory; `capacity_tib` was rejected as unsupported; seven units returned 700 CZK net as last-known, no fresh winner; all three disabled sources were identified correctly. No purchase or account write occurred.
- Skill behavioral baseline missed switching from discovery to listing for “all”; after reading the skill, the fresh-context test selected schema discovery plus exhaustive listing and separate unknowns. Both versions correctly rejected unsupported purchases and incomparable quotes.
- Plugin/MCP JSON validated against vendored Agent Plugins 1.0 upstream schemas. Plugin and resource skills use identical source bytes. Portable plugin installation/authentication in the user's Codex configuration was deliberately not performed.

Repeat automated validation:

```sh
uv run ruff check .
uv run pytest -q
docker build -t suppliermcp:local .
uv run python scripts/smoke.py
```

`uv run python scripts/codex_acceptance.py` additionally requires an installed/logged-in Codex CLI and writes temporary traces under the ignored execution workspace. It uses only synthetic catalog data and does not alter user config. Traces are not committed because client/session metadata is unnecessary for the repository.

## Remaining acceptance gates

Real account credentials and live supplier acceptance are pending: exact schemas, permitted windows and export types, redirect download hosts, commodity completeness, native attribute/packaging mappings, ValuePack formula, and source freshness semantics. Fixture-derived code must be checked against actual accounts before enabling scheduled imports. Unknown mappings remain unknown instead of invented facts.

No tunnel, public deployment, plugin installation, production load/capacity test, backup restore drill or real-catalog relevance measurement was performed. Index rebuild currently delays import publication; large catalogs require measuring that duration. Exact lookup/filtering continue without Typesense, but database failure makes catalog tools unavailable. A cached offer cannot be read when the authoritative database itself is down.

Known operational limits: API errors are structured under `result.error` (MCP transport `isError` is currently false); clients must inspect the error object. Oversized individual product details fail visibly at the response budget. Unmapped native fields are text, not invented typed common attributes. Old Typesense collections require administrative cleanup after successful rebuilds.

Pre-review baseline: `uv run ruff check .` passed; `uv run pytest -q` passed 80 tests with no skips in 5.25 seconds. Final review fixes and final counts, if any, are recorded below.

## Whole-branch review and fix evidence

A fresh-context gpt-6-astra review found nine Important issues, no Critical issues. All nine entered one implementation fix pass, with failing regression tests observed before fixes; no second review was requested. Fixes cover monotonic unchanged-run fences, independent stock evidence, per-domain/catalog completeness, accumulated descriptions in indexing, mapped packaging for matching, verified offer configuration, terminal staging cleanup, continuous bulk indexing, and per-product comparison failures. The final expanded suite passes 92 tests (6.88 seconds, no skips); `ruff check` passes. A related regression additionally prevents newer stock-only evidence from replacing ValuePack rules or price freshness.

One Minor finding is deferred: text discovery against an existing empty index returns an empty non-exhaustive result instead of `catalog_not_populated`. Exact lookup/listing already return that explicit state.

After the fix pass, the image was rebuilt and the authenticated disposable Compose smoke passed again, including restart persistence. Both actual Codex sessions were rerun successfully (exit 0): six completed tool calls without skills and eight with canonical project skills. Their outputs preserved SKU zeros, rejected the unsupported filter, and correctly labeled stale prices and disabled sources. No second code review was performed; regression tests and the full green suite are the fix verification.
