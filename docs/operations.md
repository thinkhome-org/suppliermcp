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

Discovery returns at most 1,000 confirmed ranked matches. With filters, it can scan further candidates to verify eligibility and count unknowns. It reports truncation and index lag. Use exact/list tools when Typesense is unavailable. Lists materialize at most 100,000 rows; larger results return exact count and inclusive/exclusive source-ID partitions. Pages last 30 minutes, hold at most 20 rows, and reduce rows to respect response size. Request cursors without changed filters; another identity cannot reuse them. Oversized individual products return a visible size error, never silent description truncation.

Only verified common fields support numeric filters. Native unmapped fields remain source-scoped text. Category-specific mappings must be verified before enabling category schema. The committed map starts empty: no invented RAM/capacity/category facts.

## Acceptance

Synthetic tests do not validate actual account schemas, windows, commodity coverage, discount formulas, scale or real relevance. No production credentials, supplier writes, public tunnel or deployment are exercised. See `docs/validation.md` for the actual evidence and remaining gates.


Quarantined database staging is deliberately retained until an operator reviews the import; it is not automatically discarded. Accepting the import removes its staged rows. If rejecting it, retain the compact import metadata and remove the associated staging rows through controlled database maintenance. Monitor PostgreSQL capacity while quarantine is unresolved. Terminal unchanged/superseded imports remove their staging immediately and keep compact audit records.

Source status retains separate domain outcomes and the last verified complete catalog revision. A successful stock request cannot make an unknown/partial catalog complete. Every configured but never fetched interface reduces coverage. Price evidence, stock evidence and transport fetch times are independent.

## Isolated local runtime

ThinkHome operates the v2 services in [Portainer](portainer.md). The following procedure reproduces the standalone Compose setup used for v1 validation. It uses project `suppliermcp-live` and dedicated named volumes, separately from `suppliermcp-test`. Choose a protected operator directory for configuration: `runtime.env` holds supplier/database credentials and the public verifier key; `source-contracts.json` holds verified account method windows and schedules; `signing-key.pem` and `client.env` are host-only signing/client credentials. The private key is never mounted into either application container. Do not commit or print these files.

From the repository, after setting `SUPPLIERMCP_ENV_FILE` and `SUPPLIERMCP_CONTRACTS_FILE` to the protected files:

```sh
docker compose --project-name suppliermcp-live --env-file "$SUPPLIERMCP_ENV_FILE" up -d --build
docker compose --project-name suppliermcp-live --env-file "$SUPPLIERMCP_ENV_FILE" exec worker python -m suppliermcp.worker refresh ed_public
docker compose --project-name suppliermcp-live --env-file "$SUPPLIERMCP_ENV_FILE" exec worker python -m suppliermcp.worker refresh mega --endpoint StoItemBase
```

The last command is permitted only within the verified full-export window. Outside it, the scheduler records `outside_supplier_window` and `next_allowed_at`. Do not bypass windows by looping targeted reads. One canonical representation per scheduled family is used; equivalent `_El` variants remain available for explicit product-only probes. PUBLIC catalog refreshes hourly; 100MEGA baseline daily, prices/stock hourly, selected enrichment daily. eD PRIVATE is disabled until separately configured. The initial budget is 1 GiB compressed/downloaded, 2 GiB expanded and 20 GiB retained artifacts, rather than assuming one account's measured export size is a universal maximum.

MCP is bound only to `http://127.0.0.1:8000/mcp`. `/health/live` checks the process and `/health/ready` checks the database, neither proves supplier/catalog completeness. Use `get_catalog_status` for endpoint coverage. No tunnel is provisioned. Restart with `docker compose ... restart`; do not use `down -v`, which deletes retained catalogs.

A failed publication keeps its staged import and raw artifact. After fixing the cause, `python -m suppliermcp.worker resume-import RUN_ID` publishes that retained run and reconciles endpoint status without fetching again or changing its original source/fetch evidence time. It does not bypass quarantine; only the separate `accept-import RUN_ID --reason ...` operation does. Never use an acceptance override merely to hide an incomplete or malformed download.

Large downloads use a 300-second inactivity/read timeout (`SUPPLIERMCP_DOWNLOAD_TIMEOUT_SECONDS`, configurable up to 900), with a 10-second connection timeout. Small SOAP/status requests retain the client timeout. This avoids rejecting a valid bulk export merely because its first byte takes more than 30 seconds. Each actual 100MEGA request, including retries and redirects, rechecks its mode-specific allowed window. No request is intentionally started after the window closes.

### Moving a populated v1 catalog to v2

A v1 product, price, or dictionary entry can originate under a noncatalog XML ancestor. The stored row cannot prove where it came from. On a populated legacy database the v2 migration exits with `catalog_reprojection_required` and rolls back. The v1 stack and its data remain usable. The v2 API, readiness probe and index builder require a database initialized with `011_clean_catalog.sql`.

Build the candidate on new PostgreSQL, Typesense and artifact volumes. With the local Compose stack, choose a unique project name and a free candidate port. The example uses a private runtime environment file and a port override. Replace the two paths with your configuration files.

```sh
export SUPPLIERMCP_ENV_FILE=/absolute/path/to/runtime.env
export SUPPLIERMCP_CONTRACTS_FILE=/absolute/path/to/source-contracts.json
candidate_project=suppliermcp-green
# Proceed with this project name only when this prints no existing volumes.
docker volume ls -q --filter "label=com.docker.compose.project=$candidate_project"
override_file=$(mktemp)
cat > "$override_file" <<'YAML'
services:
  mcp:
    image: suppliermcp:green-local
    ports: !override ["127.0.0.1:18000:8000"]
  worker:
    image: suppliermcp:green-local
YAML
green() {
  docker compose --project-name "$candidate_project" --env-file "$SUPPLIERMCP_ENV_FILE" \
    -f compose.yaml -f "$override_file" "$@"
}
green build worker
green up -d postgres typesense
green run --rm worker python -m suppliermcp.worker migrate
green run --rm worker python -m suppliermcp.worker refresh ed_public
# Run each configured 100MEGA endpoint inside its verified window.
green run --rm worker python -m suppliermcp.worker refresh mega --endpoint StoItemBase
green run --rm worker python -m suppliermcp.worker rebuild-index
green up -d mcp worker
curl --fail http://127.0.0.1:18000/health/ready
```

For installations with eD PRIVATE enabled, run its catalog refresh as well. Check authenticated catalog status and known SKU, current offer evidence, filtered listing, and search on the candidate. Verify required endpoint coverage before changing the client URL or reverse proxy. Keep the v1 stack, database, index and artifacts during acceptance. Rolling back means pointing clients back at the original stack. A copied v1 database, an old Typesense collection or a v1 result cursor cannot establish projected provenance.

For the stable promotion procedure, see [Promote SupDB 2.0.0](stable-release.md).

### Resuming an interrupted eD PRIVATE catalog

Apply the candidate's migrations before starting its worker. The normal
`python -m suppliermcp.worker refresh ed_private --domain catalog` command resumes
the open baseline. It requests only outstanding commodity codes, then refreshes
the dictionaries. The scheduler also retries an unfinished cycle. Another live
refresh owns the source lock if the command reports `refresh_in_progress`.

Use this read-only query on the green database to check progress and validated
empty responses. The baseline run ID identifies one frozen set of requested
codes. The worker commits each receipt with the product changes.

```sql
SELECT c.baseline_run_id, c.finished, count(*) AS expected,
       count(p.chunk_run_id) AS published,
       count(*) FILTER (WHERE p.empty) AS valid_empty
FROM ed_commodity_cycles c
JOIN ed_commodity_parts p USING (baseline_run_id)
JOIN import_runs r ON r.id=c.baseline_run_id
GROUP BY c.baseline_run_id, c.finished, r.manifest->>'started_at'
ORDER BY r.manifest->>'started_at' DESC LIMIT 1;
```

RC5 did not persist which code produced each chunk. The first upgraded cycle
requests all codes again. A completed cycle proves eD commodity coverage for
that baseline. Verify the active search index separately before acceptance.
