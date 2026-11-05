# Implementation decisions

These rulings supplement the approved design, in execution order. Each includes rationale and cost if wrong.

1. Start the installed OrbStack runtime for disposable integration services — required Docker was stopped — consumes local resources but does not deploy or alter supplier systems.
2. Add SchemaRecord to ParsedRecord — schema dictionaries/relationships cannot truthfully be encoded as products — downstream publication must handle a third record kind.
3. Freshness deduplication and SKU/ProId collision handling are verified at publication in Task 5, where prior state exists — stateless parsing cannot prove freshness — missing publication checks would invalidate last-known guarantees.
4. Require explicit account-verified I6WS contract configuration instead of guessing ResultTypeInfo HTML semantics — no authenticated schema or sample is available and access was deferred — live onboarding must establish supported result types/windows before refresh can run. Keep discovery marked unknown until configured.
5. Add interface-scoped source_presence — a PUBLIC full export must not remove PRIVATE-only items — catalog visibility is the union of successfully published interface membership; incorrect membership could retain unavailable items.
6. Use scalar SOAP envelopes for the allowlisted eD reads — public WSDL verified namespace/argument order and no complex request types are needed — WSDL contract drift must be caught by live acceptance.
7. I6WS verified intervals and allowed windows come from a mounted source-contracts JSON file — user deferred account access and we must not invent schedules — no configured schedule means no automatic source polling.
8. Add inclusive source_id_from and exclusive source_id_to to CatalogQuery — the required deterministic oversized-result partitions need a queryable boundary — clients must preserve both bounds when iterating partitions.
9. Reject category-specific schema until a verified mapping exists, retain all native fields globally — no category meaning can be inferred from unverified codes — category-specific discovery remains unavailable until source mappings are supplied.
10. Index rebuild holds the publication lane through streaming import and alias swap — simplest correct catch-up prevents revision regression without a second journal — large rebuilds delay publication while reads continue; optimize only after measured catalogs.
11. Shared accent folding and a small versioned bilingual token map replace engine-managed synonyms — same normalization on documents and queries, no optional extension — inflections outside the explicit map may require additional search terms.
12. Portable Agent Plugins 1.0 package with separately configured client bearer auth — upstream schema forbids proprietary auth extensions in MCP entries — clients unable to configure portable-plugin auth must use the TOML connection plus project skills.
13. Apply Ruff formatting and explicit repository lint rules across existing implementation — readable reviewed code and reproducible CI independent of machine-wide config — larger formatting diff, no intended behavior change.
14. Store each artifact occurrence separately with content hash plus unique suffix, and serialize global retention with a filesystem lock — shared hashes must not overwrite another domain's retention pin — identical downloads consume additional disk until retention removes older successes.
15. Reject HTTP content encoding other than identity, while retaining explicit ZIP export support — prevents automatic HTTP decompression before byte limits — suppliers ignoring Accept-Encoding require a verified bounded decoder before use.
16. Complete PRIVATE catalog refresh includes commodity enrichment plus navigator/producer/commodity/relationship dictionaries; successful chunks publish independently and failures mark partial — baseline alone lacks usable private prices — a partially unavailable dictionary reduces coverage without removing baseline products.
17. Verified native category identifiers can expose schema and explicit versioned numeric mappings are supported; no category membership or unit is inferred — extends Task 7's unknown-category behavior safely — mapping mistakes can change filter meaning and require source-specific review.
18. Actual supplier schema/permission/field/window validation remains pending — user explicitly deferred account access — synthetic compatibility is not production certification.
19. Real-catalog relevance and capacity measurement remain pending — no representative authorized catalog exists — synthetic query coverage cannot establish real recall or latency.
20. Public deployment, tunnel and token issuance remain outside this delivery — user requested repository work only — external connectivity still requires operational setup.
21. ValuePack formula remains unknown until supplier evidence verifies it — guessing could misprice orders — some quantity totals remain unavailable by design.
22. Add independent stock_evidence_at and identified per-item Comparison errors — price evidence must not be refreshed by stock, and one missing item must not erase successful batch results — clients should consume additive fields and per-item errors.

## Deferred minors

- Empty-catalog text search with an existing empty index returns empty candidates rather than catalog_not_populated; exact/list already report the explicit state.
