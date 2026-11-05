# Codex connection

The server uses Streamable HTTP with a signed RS256 bearer token. Supply a token from your identity issuer in `SUPPLIERMCP_TOKEN`; never commit tokens. Copy the example TOML into the desired isolated Codex profile after review. The ThinkHome deployment uses `https://suppliermcp.thinkhome.org/mcp` through the existing Cloudflare connector; see [Portainer deployment](../../docs/portainer.md).

Tools work without skills. To package the two optional canonical skills:

```sh
python integrations/codex/build_plugin.py /tmp/suppliermcp-plugin --url https://your-endpoint.example/mcp
```

This builds a portable Agent Plugins 1.0 package. Its JSON manifests are validated against vendored upstream schemas in tests. The package intentionally contains no credentials or token interpolation. Configure bearer authentication separately in the client. Do not enable both plugin MCP wiring and an identical manual MCP entry unless you want duplicate tool registrations. For clients that cannot configure authentication for a portable package, use the TOML connection and copy only the skills into that client's project skill directory.

For the native Codex plugin, add `--codex`. This writes `.codex-plugin/plugin.json`, `.mcp.json`, and the same two skills. The bundled HTTP connection reads `SUPPLIERMCP_THINKHOME_TOKEN` from the Codex process environment; it contains no token. Load your protected token before launching Codex. The native format is validated by the packaging test and by installing it with the Codex CLI.

The GitHub release's Codex archive includes a local marketplace. Extract it, then install from the extracted root:

```sh
codex plugin marketplace add /absolute/path/to/suppliermcp-codex-1.0.0
codex plugin add suppliermcp@thinkhome-suppliermcp
```

Restart an already running desktop client to load the plugin and MCP configuration. To use an existing authenticated `mcp_servers.suppliermcp` connection instead of supplying an environment variable to the desktop process, disable only the bundled duplicate connection:

```toml
[plugins."suppliermcp@thinkhome-suppliermcp".mcp_servers.suppliermcp]
enabled = false
```

The plugin's skills remain enabled. Keep authentication in the client's protected configuration, never in a release archive or a marketplace manifest. Installation of a local/GitHub package is separate from publication in the public OpenAI plugin directory.

Sources checked 2026-11-05: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Agent Plugins schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json). MCP resources expose identical skill text, but automatic loading of remote skills is not assumed.

The local live profile is `/Users/samuel/.local/share/suppliermcp-live/codex.toml`, with `http://127.0.0.1:8000/mcp` and `bearer_token_env_var = "SUPPLIERMCP_TOKEN"`. Load the protected `client.env` into the launching process and add this named entry to the chosen Codex profile. Keep the existing edshop server entry intact. The initial local token expires after 30 days; renew it using the host-only signing key and the same subject/issuer/audience. Supplier passwords are never sent to Codex.

The separate ThinkHome server profile is `/Users/samuel/.local/share/suppliermcp-thinkhome/codex.toml`. Its sibling `client.env` supplies `SUPPLIERMCP_THINKHOME_TOKEN`; the initial token expires after 30 days. Do not use the local server's token for this deployment, and do not upload the sibling `signing-key.pem` to Portainer. On the operator's Mac, the authenticated HTTPS connection is installed in the mode-0600 global Codex configuration, with the plugin's duplicate MCP connection disabled. Renew the stored client token before expiry; the global header and protected token file must be updated together.
