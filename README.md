# SupplierMCP

Read-only supplier catalog MCP for Codex. eD PUBLIC, eD PRIVATE and 100MEGA are independently optional. PostgreSQL retains supplier evidence and last-known offers; Typesense supports non-exhaustive text discovery. Exact lookup and typed listing work without Typesense.

Seven tools: `lookup_products`, `search_products`, `list_products`, `get_product`, `get_catalog_schema`, `compare_offers`, `get_catalog_status`.

- Supplier-only facts, conservative variant matching, explicit unknowns and freshness.
- Immutable 30-minute result pages, principal-bound cursors and separate unknown matches.
- Quantity-aware net offer comparison, known fees included; no shipping calculation or basket optimization.
- No writes to suppliers; no order, invoice, delivery or claim access.

## Connect Codex

Download the native Codex ZIP from the [v1.0.0 release](https://github.com/thinkhome-org/suppliermcp/releases/tag/v1.0.0), extract it, and run the following commands from its marketplace root:

```sh
codex plugin marketplace add "$PWD"
codex plugin add suppliermcp@thinkhome-suppliermcp
```

Set `SUPPLIERMCP_THINKHOME_TOKEN` in the environment that launches Codex, then restart Codex. Ask the server operator for a client token. You can test the connection by asking Codex to search for an SSD separately at eD and 100MEGA. For your own server, follow the Docker instructions below and [build the plugin for your MCP URL](integrations/codex/README.md).

## Local development

```sh
uv sync --locked
docker compose -f compose.test.yaml up -d --wait
uv run pytest -q
uv run ruff check .
```

Tests require disposable PostgreSQL and Typesense; missing infrastructure fails visibly. The test catalog is synthetic and does not establish real supplier API compatibility.

## Docker

Copy `.env.example` to `.env`, replace the database/index secrets and configure the public verification key. Leave supplier credential pairs absent until ready. See [operations](docs/operations.md) before starting imports.

```sh
docker compose build
docker compose up -d postgres typesense
docker compose run --rm mcp python -m suppliermcp.worker migrate
docker compose up -d mcp worker
```

Only `127.0.0.1:8000` is published. Connect to `http://127.0.0.1:8000/mcp` with a valid bearer token. Issuance, tunnel and deployment are outside this repository's setup. [Codex setup and optional skills](integrations/codex/README.md).

See [supplier contracts](docs/supplier-contracts.md), [approved design](docs/superpowers/specs/2026-11-05-suppliermcp-v1-design.md) and [compatibility](docs/compatibility.md). Live-account acceptance and real-catalog relevance remain required before production use.

Copyright © ThinkHome s.r.o. All rights reserved.
