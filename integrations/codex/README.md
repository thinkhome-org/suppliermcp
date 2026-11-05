# Codex connection

The server uses Streamable HTTP with a signed RS256 bearer token. Supply a token from your identity issuer in `SUPPLIERMCP_TOKEN`; never commit tokens. Copy the example TOML into the desired isolated Codex profile after review. The ThinkHome deployment uses `https://suppliermcp.thinkhome.org/mcp` through the existing Cloudflare connector; see [Portainer deployment](../../docs/portainer.md).

Tools work without skills. To package the two optional canonical skills:

```sh
python integrations/codex/build_plugin.py /tmp/suppliermcp-plugin --url https://your-endpoint.example/mcp
```

This builds a portable Agent Plugins 1.0 package. Its JSON manifests are validated against vendored upstream schemas in tests. The package intentionally contains no credentials or token interpolation. Configure bearer authentication separately in the client. Do not enable both plugin MCP wiring and an identical manual MCP entry unless you want duplicate tool registrations. For clients that cannot configure authentication for a portable package, use the TOML connection and copy only the skills into that client's project skill directory.

Sources checked 2026-11-05: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Agent Plugins schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json). MCP resources expose identical skill text, but automatic loading of remote skills is not assumed.

The local live profile is `/Users/samuel/.local/share/suppliermcp-live/codex.toml`, with `http://127.0.0.1:8000/mcp` and `bearer_token_env_var = "SUPPLIERMCP_TOKEN"`. Load the protected `client.env` into the launching process and add this named entry to the chosen Codex profile. Keep the existing edshop server entry intact. The initial local token expires after 30 days; renew it using the host-only signing key and the same subject/issuer/audience. Supplier passwords are never sent to Codex.

The separate ThinkHome server profile is `/Users/samuel/.local/share/suppliermcp-thinkhome/codex.toml`. Its sibling `client.env` supplies `SUPPLIERMCP_THINKHOME_TOKEN`; the initial token expires after 30 days. Load that protected environment into the client process. Do not use the local server's token for this deployment, and do not upload the sibling `signing-key.pem` to Portainer. The client profile is prepared, not automatically added to the global Codex configuration.
