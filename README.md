# SupDB · SupplierMCP

SupplierMCP 2.0 is a release candidate for read-only access to eD PUBLIC, eD PRIVATE and 100MEGA. Enable each interface independently. The catalog retains supplier evidence and last-known offers in PostgreSQL. Typesense powers text discovery. Exact lookup and complete typed listing also work when Typesense is unavailable.

## Connect to the ThinkHome candidate

ThinkHome runs the MCP server, worker, PostgreSQL catalogue and Typesense index in Portainer. Codex on the Mac connects to [SupDB MCP](https://supdb.thinkhome.org/mcp) as `supdb_v2`. To check the connection, ask “Use supdb_v2 to get the catalog status.” In personal ChatGPT, open **Plugins → Add → Add custom MCP server**, enter that URL, choose OAuth, and sign in using your registered client. The server uses a dedicated [SupDB login](docs/login.md). Applications connecting to the hosted HTTP API can inspect its [OpenAPI documentation](https://supdb.thinkhome.org/v2/docs).

The [acceptance record](docs/supplier-api/v2-acceptance.md) identifies the tested builds, client checks and deployment state. The [operation results](docs/supplier-api/operation-reads.md) distinguish live responses, account denials, supplier errors and missing test inputs. Supplier operation results and background catalog imports are tracked separately.

## Interfaces

| Client | Entry point |
| --- | --- |
| Python 3.12 | Install the candidate wheel, then import `CatalogService` from `suppliermcp.service`. Supply settings and an authorized identity. |
| REST | See `/v2/docs` or `/v2/openapi.json`. Submit catalog requests to `POST /v2/catalog/{tool_name}`. Discover supplier operations with `GET /v2/operations` and invoke an allowed read with `POST /v2/operations/{operation_id}/read`. |
| MCP | Connect to `/mcp` over Streamable HTTP. Codex and ChatGPT OAuth setup is in the [login guide](docs/login.md). |

Choose `lookup_products` for exact identifiers (preserve leading zeros), `search_products` for ranked text matches, and `list_products` for complete results within known filters. Check available filter fields with `get_catalog_schema`.

The seven catalog tools are `lookup_products`, `search_products`, `list_products`, `get_product`, `get_catalog_schema`, `compare_offers` and `get_catalog_status`. Use `list_operations` and `read_operation` for supplier-specific reads. The registry identifies allowed operations, required arguments and scopes. Account permissions and supplier availability determine which reads can return live data.

Ordinary registered clients receive catalog access. Document reads require a trusted registration for the subject and client, plus the signed `documents:read` scope. Supplier writes are blocked. PostgreSQL stores the latest catalog. Documents and addresses are fetched on demand. Catalog prices carry freshness and provenance. Quantity comparisons account for known fees and packaging, and exclude shipping.

## Connect Codex

For an existing `supdb_v2` connection, use the tools directly. For another client, follow the [remote connection guide](integrations/codex/README.md). To install the optional Codex plugin, download the native Codex ZIP for your server version from [GitHub Releases](https://github.com/thinkhome-org/suppliermcp/releases). Extract it and run these commands in the extracted marketplace directory:

```sh
codex plugin marketplace add "$PWD"
codex plugin add suppliermcp@thinkhome-suppliermcp
```

For the ThinkHome bearer-token connection, set `SUPPLIERMCP_THINKHOME_TOKEN` in the environment that launches Codex, then restart Codex. Both release ZIPs target the ThinkHome endpoint. For a different server, [build the plugin with your MCP URL](integrations/codex/README.md).

## Development server

Use this procedure for an isolated development installation. ThinkHome client machines connect to Portainer over HTTPS.

Copy `.env.example` to `.env`, set the database and index secrets, configure token verification and register your clients. Leave supplier credentials absent for an empty catalog. See [operations](docs/operations.md) before importing data.

```sh
docker compose build
docker compose up -d --wait postgres typesense
docker compose run --rm mcp python -m suppliermcp.worker migrate
docker compose up -d mcp worker
```

The default local origin is `http://127.0.0.1:8000`. For a hosted installation see the [Portainer guide](docs/portainer.md).

## Test and release

```sh
uv sync --locked
docker compose -f compose.test.yaml up -d --wait
uv run pytest -q
uv run ruff check .
```

CI uses a synthetic catalog. Candidate tags run validation before publishing a multi-architecture GHCR image. The prerelease includes the Python wheel, native and portable plugin ZIPs, checksums and the digest used for its image smoke test. Production promotion requires separate live acceptance.

Follow implementation and live verification in the [SupDB project board (organization access required)](https://github.com/orgs/thinkhome-org/projects/2). See the [Wiki](https://github.com/thinkhome-org/suppliermcp/wiki), [supplier operation inventory](docs/supplier-api/README.md), [validation evidence](docs/validation.md) and [v2 design](docs/superpowers/specs/2026-11-06-supdb-v2-design.md).

Copyright © ThinkHome s.r.o. All rights reserved.
