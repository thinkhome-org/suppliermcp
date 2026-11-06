# ThinkHome Portainer deployment

Target: Docker Standalone in ThinkHome Portainer, stack `suppliermcp`, with public MCP at `https://suppliermcp.thinkhome.org/mcp`. This is a clean installation: use fresh stack-scoped volumes and download catalogs again. Do not import the Mac database or reuse another application's volumes.

## Build and deploy

The `validate` workflow runs tests, builds the Dockerfile and boots disposable local/Portainer stacks. After a successful main-branch push validation, `publish-image` builds linux/amd64 and linux/arm64 images and publishes a commit-SHA tag to `ghcr.io/thinkhome-org/suppliermcp`. Its job summary contains the immutable digest reference. Package access remains private by default; verify publication and configure a registry identity that can read this package. Public Git repository access does not imply private registry access.

In Portainer, add a Git source named `suppliermcp` pointing to `https://github.com/thinkhome-org/suppliermcp.git`. The repository is public, so Git authentication is unnecessary; keep TLS verification enabled. Create the `suppliermcp` stack from that source, reference `refs/heads/main`, Compose path `compose.portainer.yaml`. Select the existing authenticated GHCR registry. Do not enable automatic GitOps redeployment for the initial rollout.

The target needs Compose support for config `content` (Docker Compose 2.23.1 or later). Nonsecret contract JSON is included in an application service label so changing it recreates MCP/worker and mounts the new configuration during a normal update. Never put credentials in that contract. Config JSON is delivered as `/config/source-contracts.json`; no Mac paths or Git-relative bind mounts are needed. Verify the mounted JSON before declaring ingestion ready.

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

eD PRIVATE is deliberately not configured in this deployment. Keep JWT signing keys and client bearer tokens outside the application containers. Tokens require RS256, subject, expiry, issuer `suppliermcp` and audience `suppliermcp`. The public client profile uses the HTTPS URL above and a bearer token supplied through the client's protected environment.

The image does not contain source credentials, source contracts or client tokens. The initial download limit is 1 GiB, expanded XML limit 2 GiB and retained-artifact budget 20 GiB. Database/index disk usage is additional; the measured full local catalog occupied many gigabytes.

## Startup and routing

PostgreSQL must become healthy, then the one-shot `migrate` service must exit 0. MCP and worker start only after migrations succeed. A healthy MCP container proves liveness; `/health/ready` verifies database readiness, not catalog population.

Reuse the existing `cloudflare` network and connector stack. Only MCP joins that external network, under the alias `suppliermcp-origin`. PostgreSQL, Typesense and worker stay on the stack's backend network; no service publishes a host port. Configure the existing tunnel's published application route:

- Hostname: `suppliermcp.thinkhome.org`
- Service: `http://suppliermcp-origin:8000`
- Client URL: `https://suppliermcp.thinkhome.org/mcp`

Keep application bearer authentication enabled. Avoid an interactive browser-login challenge on `/mcp` unless the chosen MCP client is explicitly configured for it. The tunnel token belongs to the existing connector stack, never this repository or SupplierMCP variables.

## Acceptance and operations

The ThinkHome stack was installed with fresh volumes on 2026-11-05/06 in Portainer environment 3, stack 24. Its validated image is pinned to `ghcr.io/thinkhome-org/suppliermcp@sha256:451fd11823f9a3ee72acb2a3737d162d9d21fb174dd2253b1fb358c3e0fe0f23` (source commit `80bbddb`). The target pulled the image successfully, migrations exited 0, and Cloudflare created the public route and DNS record. Public liveness/readiness returned 200; missing and invalid bearer tokens returned 401; authenticated discovery returned seven tools and two resources. See [deployment evidence](portainer-deployment-2026-11-06.json) for the catalog acceptance state, which is separate from service availability.

The protected target client profile is `/Users/samuel/.local/share/suppliermcp-thinkhome/codex.toml`, with its token in the sibling `client.env`. These files are local operator artifacts, not repository content. The initial client token lasts 30 days; renew it with the host-only signing key before expiry.

Verify unauthorized `/mcp` access returns 401 and authenticated clients discover seven tools and two skill resources. Run `scripts/live_verify.py --url https://suppliermcp.thinkhome.org/mcp --report /protected/path/report.json` with `SUPPLIERMCP_TOKEN` supplied privately. Inspect the report's checks, not merely process exit status.

After the fresh import, compare authoritative active product counts with index document counts and inspect `get_catalog_status` endpoint outcomes/revisions. A running worker is not proof of a populated catalog. Night-only exports wait for their permitted Europe/Prague windows; unavailable/disabled interfaces must remain visible without hiding retained results. Do not bypass windows with repeated targeted reads.

Do not use `down -v` on the real stack. To update, select a newly validated immutable image digest, review migrations, redeploy and check health/auth/index status. Keep the old digest for application rollback; database migration rollback requires an appropriate database backup and restore procedure, not just an old image.

## Reproduce infrastructure validation

```sh
docker build -t suppliermcp:portainer-test .
uv run pytest tests/test_portainer.py -q
uv run python scripts/portainer_smoke.py
```

The smoke creates its own randomly named project/network, generates ephemeral test credentials, makes no supplier requests, reproduces the Portainer UI/backend environment path, verifies mounted configuration, literal special characters and authenticated access, and removes only its own disposable volumes.

Sources: [Portainer Git stacks and variables](https://docs.portainer.io/user/docker/stacks/add), [Docker Compose configs](https://docs.docker.com/reference/compose-file/configs/), [Cloudflare application routes](https://developers.cloudflare.com/tunnel/get-started/).

When upgrading an existing index, the worker automatically rebuilds collections that lack the supplier filter field. Let that rebuild finish before starting another. A rebuild temporarily holds two copies. Check available RAM, the active Typesense alias, its supplier facet, the document count against active PostgreSQL products and the catalog/index revisions. Retire obsolete generated collections only after verifying the replacement and checking every alias.
