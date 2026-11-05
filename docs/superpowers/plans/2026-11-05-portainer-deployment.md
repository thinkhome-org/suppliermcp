# ThinkHome Portainer Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a clean authenticated SupplierMCP instance at https://suppliermcp.thinkhome.org/mcp.
**Architecture:** Add a separate Docker Standalone Compose, validated/published GHCR image, migration prerequisite, and existing external Cloudflare network. Keep local runtime and data intact.
**Tech Stack:** Existing Python/FastMCP/PostgreSQL/Typesense, GitHub Actions, Docker Compose, Portainer BE, Cloudflare Tunnel.
**Spec:** docs/superpowers/specs/2026-11-05-portainer-deployment-design.md

## Global Constraints
- Fresh target volumes; do not transfer the Mac database or artifacts.
- Reuse the cloudflare network and existing connector; only MCP joins that network.
- No secrets in Git, images or logs; JWT signing key remains host-only.
- eD PUBLIC and 100MEGA configured independently; eD PRIVATE disabled.
- Respect supplier windows and report incomplete first population honestly.
- Preserve user authorization for implementation, push and deployment; browser action-time policy still applies.

## Review Focus
- Missing credentials/public key/image reference must fail before an insecure partial stack starts.
- Database/index must not join the tunnel network or publish host ports.
- Fresh migrations must finish before workers and MCP access tables.
- Structured contract JSON/public PEM must survive Compose interpolation and file delivery.
- Image publication and target pull must be independently verified, not inferred from CI YAML.

### Task 1: Package and validate the target deployment
**Files:** Create compose.portainer.yaml, .github/workflows/publish.yml, tests/test_portainer.py, docs/portainer.md; update Dockerfile/.dockerignore only if necessary.
**Interfaces:** Consume existing Settings, worker migrate/run commands and Dockerfile. Produce immutable GHCR digest, deployment variables and network alias suppliermcp-origin.
- [ ] Write rendered-Compose tests using synthetic credentials/contracts. Assert absence of host ports, isolated database/index, completed-migration dependencies, exact JSON config preservation, and failure with missing required image/key/secrets.
- [ ] Run `uv run pytest tests/test_portainer.py -q`; expect failures because the deployment file does not exist.
- [ ] Add minimal independent Compose with named volumes, config content, explicit runtime variables and existing pinned dependency images. Add publication workflow after the existing validation succeeds, only for main commits, with packages:write scoped to the publishing job and commit SHA tags.
- [ ] Run focused tests and a fresh isolated infrastructure boot. Verify health, 401 without token, authenticated seven-tool discovery and disabled-source status. Preserve real live volumes and avoid supplier calls in this test.
- [ ] Run `uv run pytest -q`, `uv run ruff check .`, Docker build. Commit deployment files and perform one independent code review before deploying them.

### Task 2: Publish, deploy, and record actual acceptance
**Files:** Update docs/portainer.md and add payload-free deployment evidence under docs/.
**Interfaces:** Consume Task 1 Compose/digest and protected target configuration. Produce target stack and authenticated HTTPS endpoint.
- [ ] Push authorized changes, verify validate/publish workflows and image digest/platform. Confirm target registry access; never make a package public silently to bypass credentials.
- [ ] Create protected deployment variables with fresh database/index secrets, public JWT key and verified account contract JSON. Keep private signing material local and credentials out of output.
- [ ] Deploy the Git stack in ThinkHome Portainer environment 3, using fresh volumes and the immutable image digest. Verify migration completion and service state.
- [ ] Prepare the exact Cloudflare hostname route; obtain only action-time confirmation required by the browser tool, then apply it and verify HTTPS authentication/tools.
- [ ] Verify fresh source requests and published/index counts, explicitly distinguish completed exports from queued/window-blocked work. Record deployment checks and operational instructions in English.
- [ ] Run relevant checks on changed code; commit and push final evidence. Keep external blockers explicit if access is unavailable.

## Self-review
The two tasks share image reference, config delivery and network alias. Task 1 establishes those contracts before Task 2 uses them. Application logic is reused. All five review-focus conditions have rendered-config, boot, or target acceptance checks; no additional supplier semantics are introduced.
