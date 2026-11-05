# Operations

## Configuration and startup

Use one `.env` file outside version control. Database passwords used in a DSN must be URL-safe or percent-encoded. Set `POSTGRES_PASSWORD`, `SUPPLIERMCP_TYPESENSE_KEY`, and a PEM `SUPPLIERMCP_AUTH_PUBLIC_KEY` (Compose supports single-quoted multiline values). Configure issuer/audience to your token issuer. Tokens require RS256, subject and expiration. The server never receives the signing private key. Default trusted hosts are localhost/127.0.0.1; JSON arrays in `SUPPLIERMCP_ALLOWED_HOSTS` and `SUPPLIERMCP_ALLOWED_ORIGINS` must name the deployed endpoint explicitly.

Apply migrations before starting server/worker. No supplier credentials are needed to start the catalog. Empty catalog operations return `catalog_not_populated`; status identifies disabled interfaces. Configured sources without imports report `not_fetched`. Readiness means database access, not supplier freshness; inspect authenticated status for source outcomes. Liveness exposes no catalog/account data.

Source schedules are opt-in through `SUPPLIERMCP_SOURCE_CONTRACTS_PATH`, a mounted JSON file. Example shape (replace with verified account settings):

```json
{"ed_public":{"download_hosts":[],"intervals_seconds":{"catalog":86400}}}
```

Do not use this sample as supplier permission to poll. Verify allowed windows, returned fields and account scope first. eD PRIVATE catalog baselines contain placeholder commercial fields. 100MEGA needs verified export modes, timezone/windows and currency/stock semantics; unknown contracts fail visibly. The adapter contract tests show the accepted `exports` format. Mount the file read-only into both application services with a Compose override. Never mount secrets into the plugin package.

## Durability and recovery

The `postgres`, `typesense`, and `artifacts` named volumes persist across ordinary restarts. Do not run `down -v` on production data. Back up PostgreSQL with `pg_dump` plus the artifacts volume and configuration stored separately in protected storage. Restore into an empty isolated database using `pg_restore`; test the restore before replacing a working instance. Retained evidence and offers are authoritative; Typesense is disposable.

Rebuild discovery after index loss:

```sh
docker compose run --rm worker python -m suppliermcp.worker rebuild-index
```

Rebuild streams database rows into a new collection and swaps the alias after full success. It serializes publication during the rebuild; existing reads remain available. Failed builds retain the old alias. Old collections may be removed administratively after confirming the alias and backup; automatic collection garbage collection is not included.

A complete catalog drop greater than 25% is quarantined. Inspect the retained artifact and import run before a deliberate override:

```sh
docker compose run --rm worker python -m suppliermcp.worker accept-import RUN_UUID --reason 'Verified supplier scope change'
```

A failed refresh keeps prior prices and marks refresh failure. Re-downloading unchanged bytes does not refresh price evidence. Last-known and fresh winners are different; missing source timestamps/fees/packaging prevent a verified total. Every product remains source-identifiable even if matching is unresolved.

## Search limits

Discovery scans at most 1,000 candidates and reports the limit, indexing lag, and non-exhaustiveness. Use exact/list tools when Typesense is unavailable. Lists materialize at most 100,000 rows; larger results return exact count and inclusive/exclusive source-ID partitions. Pages last 30 minutes, hold at most 20 rows, and reduce rows to respect response size. Request cursors without changed filters; another identity cannot reuse them. Oversized individual products return a visible size error, never silent description truncation.

Only verified common fields support numeric filters. Native unmapped fields remain source-scoped text. Category-specific mappings must be verified before enabling category schema. The committed map starts empty: no invented RAM/capacity/category facts.

## Acceptance

Synthetic tests do not validate actual account schemas, windows, commodity coverage, discount formulas, scale or real relevance. No production credentials, supplier writes, public tunnel or deployment are exercised. See `docs/validation.md` for the actual evidence and remaining gates.
