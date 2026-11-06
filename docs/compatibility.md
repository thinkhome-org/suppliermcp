# Compatibility record

Resolved on 2026-11-05 using Python 3.12.14: FastMCP 4.1.6, MCP 2.3.0,
psycopg 3.3.8, Procrastinate 3.10.0, Zeep 4.3.3. Exact transitive versions
are in uv.lock. Real authenticated Streamable HTTP tests use FastMCP Client and SDK protocol 2026-07-28. Codex session acceptance is recorded separately in validation.md. Docker uses Python 3.12.16 from its pinned multi-platform digest.
No remote skill activation is assumed.

### v1 bearer token migration

Before switching to v2, enumerate the trusted subjects of your existing unscoped
v1 tokens in `SUPPLIERMCP_AUTH_LEGACY_SUBJECTS` as a JSON array. The default
array is empty. The same signature, issuer, audience and expiry checks still
apply. These subjects receive catalog access only when the token has no client
or scope claims. Previously issued pagination cursors must be restarted after
the upgrade because v2 binds them to the issuer, subject and client together.

Register each OAuth application's issuer-assigned client ID in
`SUPPLIERMCP_AUTH_CLIENTS`, a JSON object. Use an empty object for ordinary
clients. For each personal client, set `document_subjects` to the exact subject
IDs authorized for account-wide document reads. A signed token must identify
the client via `client_id` or `azp` and carry its grants in the space-delimited
`scope` claim. A registration limits what that token may access. For example:

```json
{
  "catalog-client": {},
  "personal-codex-client": {"document_subjects": ["owner-subject"]},
  "personal-chatgpt-client": {"document_subjects": ["owner-subject"]}
}
```
