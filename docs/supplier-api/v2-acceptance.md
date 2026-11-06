# SupDB v2 candidate acceptance

## 2026-11-06, isolated stack using the ThinkHome supplier account

These observations cover the tested components and revision at the time of each check. The production service still ran v1 during these checks. [RC1](https://github.com/thinkhome-org/suppliermcp/releases/tag/v2.0.0-rc.1) ships an independently installable wheel and native/portable plugins; the published checksums were verified.

| Check | Observed result |
|---|---|
| eD PRIVATE authenticated SOAP | `getProductProducerList` returned `DONE` and 1,506 producers using the account previously used for PUBLIC. |
| Restored PostgreSQL catalogue | A transaction-consistent logical backup of the live v1 database restored into a separate PostgreSQL instance. Migration 009 preserved all 157,841 active IDs, verified by hashing the ordered ID list before and after. Migration 011 subsequently refused the populated clone and left the ID digest and prior applied migration intact. V2 imports catalogue data into a fresh database; copy-forward of ambiguous legacy XML-derived rows is intentionally blocked. |
| Python/REST/MCP parity | The regression suite exercised the seven catalogue functions, supplier-operation argument validation, client scopes and cross-client continuation rejection. |
| REST with live supplier data | The registered catalogue client read the private product-producer list and received HTTP 403 on the invoice-list operation. The personal client successfully called both operations. |
| Actual Codex CLI | An ephemeral Codex session invoked the local candidate by Streamable HTTP. Trace inspection confirmed completed calls to eD PRIVATE transportation and eD PUBLIC invoice-list reads. This first check used a locally signed access token. A subsequent Codex CLI run called both catalogue and document operations on the authorized temporary HTTPS MCP endpoint using a Keycloak-issued token (specifically the eD PRIVATE transportation list and eD PUBLIC invoice list). |
| Personal ChatGPT web interface | The signed-in personal web account exposed **Plugins → Add → Add custom MCP server**, with a server URL and OAuth option. This was a capability check only. A connected account read requires a reachable candidate and consent. |
| Dedicated login | A disposable Keycloak 26.8.2 realm completed an authorization-code exchange with PKCE S256 for personal and ordinary test registrations. The application verifier checked the issuer, signing key, audience, subject and grants. The ordinary client had only catalogue access. The subsequent temporary HTTPS deployment verified PKCE, remote JWKS, protected-resource discovery, 401 for unauthenticated MCP, a live document read for the personal client, 403 for the ordinary client, and 404 on the public identity-provider administration route. The public HTTPS checks were repeated using the wheel downloaded from the RC1 release with its SHA-256 verified. ChatGPT web consent is tracked separately. |
| Rollback rehearsal | The Portainer Compose definition ran in an isolated local Docker stack using a rebuilt image from the deployed v1 source revision. After migration 011 refused a populated v1 database, a fresh, isolated v2 stack started and restarted successfully. A v1 PostgreSQL backup restored into fresh storage and an authenticated lookup through the restored v1 image found the original synthetic SKU. Release CI repeats this test using the published v1 digest. |
| Production v1 | The existing HTTPS readiness endpoint returned 200. No v2 production promotion was part of that check. |
| GitHub | The integrated Wiki was initialized and nine public operator/developer pages were published. The synchronization workflow ran successfully after [PR 7](https://github.com/thinkhome-org/suppliermcp/pull/7) merged. Organization Project 2 is linked to the repository, tracks the acceptance areas and has auto-add enabled for open repository issues and PRs. |

Use the per-operation evidence for claims about supplier coverage. A successful method listing, a successful XML download request, a parsed page of results and a complete import prove different things.

[Wiki](https://github.com/thinkhome-org/suppliermcp/wiki) · [Release project](https://github.com/orgs/thinkhome-org/projects/2) · [Candidate pull request](https://github.com/thinkhome-org/suppliermcp/pull/6)


## Published RC3 and the clean catalogue

[RC3](https://github.com/thinkhome-org/suppliermcp/releases/tag/v2.0.0-rc.3) passed CI, CodeQL and the published-digest smoke/rollback job. The SHA-256 checksums of the downloaded wheel, native and portable plugin archives, and image reference were verified locally. RC2's release job stopped at a version mismatch before publishing artifacts; RC3 derives both plugin versions from package metadata.

The temporary HTTPS endpoint was switched to the verified RC3 wheel. On this endpoint a Keycloak-issued personal token completed an eD invoice-list read (HTTP 200); the ordinary client received HTTP 403 for the same read. An actual Codex CLI session completed eD PRIVATE transportation and eD PUBLIC invoice-list MCP calls. The catalogue library also exercised ELINKX PUBLIC/PRIVATE and an i6ws category export using their declared protocol profiles.

On the signed-in personal ChatGPT website, the operator created the cloud plugin and successfully authenticated to the temporary OAuth realm. ChatGPT presented a separate **Connect** action for chat use. The temporary window closed before confirmation of that step; no catalogue or document tool call from an ordinary ChatGPT web conversation is claimed. The temporary tunnel, both DNS records, login service and its temporary credentials were removed. Production Portainer v2 cutover remains pending access to its Docker environment. The v1 manifest retained its original bytes on main; the v2 manifest uses a separate filename and candidate origin alias.

A separate v2 database was populated through the projected adapters. Verified retained eD PUBLIC and 100MEGA source artifacts were re-parsed; the eD PRIVATE baseline and stock export were fetched from the account. At revision 11 the database contained 157,824 active products. All rows in the complete price-ordered listing matched an independent SQL calculation. [Search, index rebuild and latency evidence](v2-search-validation.md).
