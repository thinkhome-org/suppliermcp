# ThinkHome Portainer deployment

The production v1 Git stack `suppliermcp` follows `refs/heads/main` and reads `compose.portainer.yaml`. Keep that path pinned to the deployed v1 configuration. The candidate uses a separate stack, Compose file, volumes and tunnel origin. The v1 endpoint is `https://suppliermcp.thinkhome.org/mcp`. The deployed v2 candidate uses [SupDB MCP](https://supdb.thinkhome.org/mcp) and a [separate login realm](https://supdb-login.thinkhome.org/realms/supdb/.well-known/openid-configuration). See the [deployment and restart evidence](supplier-api/v2-acceptance.md#rc5-on-the-mac-and-portainer).

## Build and deploy the candidate

1. Obtain the image digest from the release's `image-reference.txt`. Candidate CI builds linux/amd64 and linux/arm64 images and runs a disposable Portainer smoke test. Select the GHCR registry identity that can pull the image.
2. In Portainer create a **new** Git stack such as `suppliermcp-green` from `https://github.com/thinkhome-org/suppliermcp.git`. Select the tested release tag under `refs/tags/` and the Compose path `compose.portainer-v2.yaml`. Keep TLS verification enabled and GitOps redeployment disabled. Use fresh stack-scoped volumes and import the catalog from the suppliers. The v2 migration refuses a populated v1 catalog.
3. Supply the selected image digest, a candidate hostname in `SUPDB_PUBLIC_HOST`, and a unique `SUPDB_ORIGIN_ALIAS` such as `suppliermcp-green-origin`. Route just that hostname to the green alias, and complete acceptance before switching the production tunnel route.
4. Use Docker Compose 2.23.1 or later for config `content`. The service label carries the nonsecret source contract JSON so updating it recreates MCP and worker. Verify the mounted file at `/config/source-contracts.json`.

## Deployment variables

Prepare a protected JSON object of the values below, then encode it for **Load variables from .env file**:

```sh
uv run python scripts/portainer_env.py /protected/deployment.json /protected/portainer.env
```

Portainer 2.45.1 imports physical lines and later writes their values directly into a dotenv file. The helper writes one physical line per value, keeps multiline PEM encoded with escaped newlines, and protects dollar signs, quotes and backslashes from interpolation. **Retain the surrounding quotes and escapes displayed in Portainer's fields.** Do not upload a conventional multiline PEM `.env` file or paste a raw PEM into a field. The helper output is mode 0600. Do not commit either populated file or include its values in screenshots or logs.

| Variable | Value |
|---|---|
| `SUPPLIERMCP_IMAGE` | Verified `ghcr.io/thinkhome-org/suppliermcp@sha256:…` digest from publication |
| `POSTGRES_PASSWORD` | Newly generated URL-safe random password; it is interpolated into a PostgreSQL URI |
| `SUPPLIERMCP_TYPESENSE_KEY` | Newly generated random index API key |
| `SUPPLIERMCP_AUTH_PUBLIC_KEY` | Full PEM verification public key, preserving newlines; never the private key |
| `SUPPLIERMCP_SOURCE_CONTRACTS_JSON` | Verified account contract object as one JSON string, including schedules and allowed windows |
| `SUPPLIERMCP_MEGA_LOGIN`, `SUPPLIERMCP_MEGA_PASSWORD` | 100MEGA account pair, or both empty |
| `SUPPLIERMCP_ED_PUBLIC_LOGIN`, `SUPPLIERMCP_ED_PUBLIC_PASSWORD` | eD PUBLIC account pair, or both empty |
| `SUPPLIERMCP_ED_PRIVATE_LOGIN`, `SUPPLIERMCP_ED_PRIVATE_PASSWORD` | eD PRIVATE account pair, or both empty |
| `SUPPLIERMCP_OAUTH_ISSUER`, `SUPPLIERMCP_OAUTH_PUBLIC_URL` | HTTPS realm issuer and public API origin for OAuth discovery and token validation |
| `SUPPLIERMCP_AUTH_CLIENTS` | Registered client IDs and permitted document subjects, as described in the [login guide](login.md) |
| `SUPPLIERMCP_READ_CURSOR_KEY` | Independent base64-encoded key of at least 32 random bytes. Retain it across API restarts for supplier-read continuations. |

For an account with eD PRIVATE access, supply both `SUPPLIERMCP_ED_PRIVATE_LOGIN` and `SUPPLIERMCP_ED_PRIVATE_PASSWORD` using protected Portainer variables. Enable the desired PRIVATE refresh intervals in the verified source contracts. See [dedicated login](login.md) for the personal ChatGPT OAuth setup. Keep JWT signing keys and client bearer tokens outside the application containers. Static tokens require RS256, a subject, expiry and the issuer and audience configured through `SUPPLIERMCP_AUTH_ISSUER` and `SUPPLIERMCP_AUTH_AUDIENCE`. OAuth tokens use the dedicated realm issuer and the public MCP URL as audience.

The image does not contain source credentials, source contracts or client tokens. The initial download limit is 1 GiB, expanded XML limit 2 GiB and retained-artifact budget 20 GiB. Database/index disk usage is additional; the measured full local catalog occupied many gigabytes.

## Startup and routing

PostgreSQL must become healthy, then the one-shot `migrate` service must exit 0. MCP and worker start only after migrations succeed. A healthy MCP container proves liveness; `/health/ready` verifies database readiness, not catalog population.

Only MCP joins the existing external `cloudflare` network. PostgreSQL, Typesense and worker stay on the stack's backend network. The v1 tunnel currently routes `suppliermcp.thinkhome.org` to `http://suppliermcp-origin:8000`. During candidate acceptance the green tunnel route uses `http://suppliermcp-green-origin:8000` and its own public hostname. After acceptance, configure the production hostname on green before switching the tunnel route. Keep the blue origin available for rollback.

Keep application bearer authentication enabled. Avoid an interactive browser-login challenge on `/mcp` unless the chosen MCP client is explicitly configured for it. The tunnel token belongs to the existing connector stack, never this repository or SupplierMCP variables.

## Acceptance and operations

The original v1 stack was installed with fresh volumes on 2026-11-05/06 in Portainer environment 3, stack 24. Its validated image is pinned to `ghcr.io/thinkhome-org/suppliermcp@sha256:451fd11823f9a3ee72acb2a3737d162d9d21fb174dd2253b1fb358c3e0fe0f23` (source commit `80bbddb`). The target pulled the image successfully, migrations exited 0, and Cloudflare created the public route and DNS record. Public liveness/readiness returned 200; missing and invalid bearer tokens returned 401; authenticated discovery returned seven tools and two resources. See [deployment evidence](portainer-deployment-2026-11-06.json) for the catalog acceptance state, which is separate from service availability.

Keep the target client profile and token in the operator’s protected directory. Renew a static client token before expiry with the host-only signing key. For web ChatGPT, use the scoped OAuth flow in the login guide.

Verify unauthorized `/mcp` access returns 401. On a v2 candidate, authenticated clients should discover the seven catalog tools plus `list_operations` and `read_operation`. Check the two skill resources as well. Run `scripts/live_verify.py --url https://<candidate-host>/mcp --report /protected/path/report.json` with `SUPPLIERMCP_TOKEN` supplied privately. Inspect the report's checks, not merely process exit status.

After the fresh import, compare authoritative active product counts with index document counts and inspect `get_catalog_status` endpoint outcomes/revisions. A running worker is not proof of a populated catalog. Night-only exports wait for their permitted Europe/Prague windows; unavailable/disabled interfaces must remain visible without hiding retained results. Do not bypass windows with repeated targeted reads.

Do not use `down -v` on the real stack. To update, select a newly validated immutable image digest, review migrations, redeploy and check health/auth/index status. Keep the old digest for application rollback; database migration rollback requires an appropriate database backup and restore procedure, not just an old image.

## Reproduce infrastructure validation

```sh
docker build -t suppliermcp:portainer-test .
uv run pytest tests/test_portainer.py -q
SUPPLIERMCP_ROLLBACK_IMAGE=ghcr.io/thinkhome-org/suppliermcp@sha256:451fd11823f9a3ee72acb2a3737d162d9d21fb174dd2253b1fb358c3e0fe0f23 \
  uv run python scripts/portainer_smoke.py
```

The smoke starts blue from the v1 production manifest and green from the v2 manifest in separate disposable Compose projects. It verifies distinct tunnel aliases on its own external network, generates ephemeral test credentials, makes no supplier requests, reproduces the Portainer UI/backend environment path, verifies mounted configuration, literal special characters and authenticated access, and removes only its own disposable volumes.

Sources: [Portainer Git stacks and variables](https://docs.portainer.io/user/docker/stacks/add), [Docker Compose configs](https://docs.docker.com/reference/compose-file/configs/), [Cloudflare application routes](https://developers.cloudflare.com/tunnel/get-started/).

When upgrading an existing index, the worker automatically rebuilds collections that lack the supplier filter field. Let that rebuild finish before starting another. A rebuild temporarily holds two copies. Check available RAM, the active Typesense alias, its supplier facet, the document count against active PostgreSQL products and the catalog/index revisions. Retire obsolete generated collections only after verifying the replacement and checking every alias.
