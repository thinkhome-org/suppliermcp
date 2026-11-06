# Catalogue query validation, 6 November 2026

## Restored v1 catalogue, revision 35

The query implementation at `e29a673` ran against an isolated PostgreSQL restore and a separate Typesense instance. The restore contained **157,841 active products**. This is a baseline for evaluating query changes. Clean v2 imports use a different catalogue and index.

| Measurement | Result |
|---|---:|
| Full index rebuild, elapsed | 1,326.18 s |
| Rebuild process, peak RSS | 1,093,812,224 bytes |
| Isolated Typesense cgroup, peak memory including cache | 2,098,466,816 bytes |
| Searches completed during a synthetic 1,000-row import | 694 |
| Search latency, p50 / p95 | 14.59 / 79.84 ms |
| Products checked against independent PostgreSQL ordering | 157,841 |
| Missing, extra or misordered product IDs | 0 |

The rebuild includes initial cold scans before PostgreSQL collected planner statistics on the restored observation table. The importer used a separate connection, staged and published synthetic data inside an outer transaction, then rolled it back. The search loop cycled through the seven queries below and excluded the final request if the import had already finished. Latencies measure full search calls, including materialization of a result snapshot.

An end-to-end check traversed all pages in a 500-product scope. A second check read every stored result ordinal in four disjoint ID partitions of 50,000, 50,000, 50,000 and 7,841 products. The independent calculation joined the resolved currency and unit-price observations, ordered CZK prices ascending, placed other or unknown prices last and broke ties by product ID. A full outer join checked both order and membership within each supported partition.

### Relevance

Seven queries and their expected model tokens were fixed before indexing. The baseline label counted a product as relevant when its supplier title contained the model token. Each vector below records relevance at ranks one through five, truncated to the number of hits returned. Product records and identifiers are omitted.

| Query intent | Title matches in PostgreSQL | Grades at returned ranks |
|---|---:|---|
| Access point with Czech category words and model | 6 | 1 |
| Access point by model alone | 6 | No hits |
| Switch with Czech category word and model | 10 | 1, 1 |
| SSD with model | 7 | 1, 1, 1, 1, 1 |
| SSD with an ambiguous model token | 1 | No hits |
| Router with Czech category word and model | 4 | 1, 1, 1, 1 |
| Router by model family and variant | 2 | 1, 1, 0 |

Five of seven queries returned a title-labelled match in their first five hits. Fourteen of the fifteen returned entries met that label. Inspection identified two different causes for the empty results. The second query's entire model token occurred immediately before a hyphen in all six matching titles. The fifth query's sole title match was an audio product. Its supplier title and evidence provided no basis for including it in an SSD search. Accordingly, the fifth case is a negative control in the subsequent evaluation. The original grades above preserve the predeclared rule.

The model-token fix in `7d5eb74` indexes whole alphanumeric model components immediately before a hyphen. A synthetic regression checks the family, the full hyphenated identifier, the compact identifier and rejection of shorter prefixes and adjacent model numbers. The numbers above predate this change.
