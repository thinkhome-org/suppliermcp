# SupplierMCP: clean ThinkHome Portainer deployment

## Confirmed intent

Deploy SupplierMCP from `thinkhome-org/suppliermcp` to the separate ThinkHome Portainer server. The user confirms the supplier-facing IP is permitted. Public MCP address: `https://suppliermcp.thinkhome.org/mcp`. Start with empty persistent volumes and download supplier catalogs again; do not transfer the Mac database or artifacts. Existing read-only product scope and optional-source behavior remain unchanged.

The authenticated Portainer UI shows Docker environment `local` (environment 3), Portainer Business 2.45.1, and an existing bridge network named `cloudflare`. These observations establish available infrastructure, not successful application deployment or supplier access from the target.

## Approach

Keep the existing local Compose workflow. Add a standalone `compose.portainer.yaml` for the target. Recommended implementation choice: GitHub Actions builds the existing Dockerfile after validation and publishes a commit-tagged image to GHCR, keeping package access private by default. Resolve and deploy an immutable image digest. Portainer retrieves Compose from Git and the image from the registry; repository and registry authentication are separate.

Alternative: build the image on the target host from a Git checkout. This avoids registry authentication but couples deployments to host build access and tooling. A local-only image tag is not a deployable artifact on another host. Do not assume a registry image exists until publication and target pull succeed.

## Services and startup

- PostgreSQL and Typesense use fresh stack-scoped named volumes and no published host ports.
- A one-shot migration service runs the existing maintenance migration command after PostgreSQL becomes healthy. MCP and worker start only after migration succeeds.
- MCP exposes its existing authenticated Streamable HTTP endpoint. Attach only MCP to the existing external `cloudflare` network, using a unique alias `suppliermcp-origin`; all application services also use the stack's own network as needed. Do not attach databases to `cloudflare`.
- The worker downloads fresh eD PUBLIC and 100MEGA catalogs using the existing verified account contracts and supplier windows. eD PRIVATE remains unconfigured.
- Configure Cloudflare's published application route for the selected hostname to `http://suppliermcp-origin:8000`. Public requests still require the application's bearer token. Preserve HTTP streaming behavior and the verified Host allowlist.
- Reuse the existing tunnel; do not deploy a second tunnel connector merely for this application. The supplied tunnel token must not enter Git, application images, or documentation.

## Configuration

Provide supplier credentials and newly generated deployment database/index secrets through protected deployment configuration. Keep the JWT signing private key off the application server; deploy only its verification public key. Prepare a separate client connection profile for the public URL. Host and Origin restrictions must include only the actual supported addresses.

Avoid Mac-specific bind mounts. Supply the verified source-contract JSON as a Compose configuration file, using the target Compose version's supported mechanism. Validate that mechanism before deployment; do not replace an unreadable configuration with an empty contract and call ingestion successful. Account contracts carry scheduling/semantics, not credentials. Keep equivalent export variants separately mapped rather than downloading every representation automatically.

Use the measured live-account download/artifact budgets as explicit initial settings. First population can be slow and is constrained by supplier windows. The empty installation must report not-fetched/partial states accurately while imports run. Readiness is distinct from full catalog and index readiness.

## Acceptance

1. Render the Portainer Compose with synthetic configuration and verify required variables, network isolation, persistent volumes, and migration ordering.
2. Boot an isolated empty local deployment using the same image and verify migration, authentication, health, and unavailable-source behavior. Do not use production supplier credentials for this infrastructure test.
3. Build and publish the real image, verify its digest/platform, and verify the target can pull it.
4. Deploy the fresh stack without modifying existing unrelated stacks or Mac volumes.
5. Configure the hostname route and verify HTTPS MCP: unauthorized requests rejected; authenticated tool/resource discovery and representative tool calls succeed.
6. Verify supplier authentication from the target, actual imports, endpoint outcomes, and database/index counts. Night-only exports and incomplete enrichment stay explicitly pending until completed.
7. Update the repository's English deployment instructions and payload-free evidence with the actual outcomes. Do not equate running containers with completed catalog acceptance.

## Boundaries

No database migration from the Mac, eD PRIVATE activation, supplier writes, unrelated Portainer upgrades, broad Cloudflare policy changes, or automatic redeployment on every push. Browser-mediated public-exposure or credential-saving actions may require an action-time confirmation under the browser tool policy; prepare the exact change before that step.

## Approval state

The user has confirmed the target, hostname, fresh-data approach, and Git/Portainer/Cloudflare objective. This short document records the proposed packaging and startup details for review before implementation.
