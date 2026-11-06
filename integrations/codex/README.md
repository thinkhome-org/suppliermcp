# Codex connection

Connect Codex to the [ThinkHome Portainer deployment](../../docs/portainer.md) over Streamable HTTP. The operator uses the server name `supdb_v2` and the URL `https://supdb.thinkhome.org/mcp`. The Mac runs the Codex client. Portainer runs catalog imports, search, storage and MCP.

For a new bearer-token client, copy the [example TOML](mcp.toml.example) into its Codex configuration and load its registered token into the launching process. For a client registered for OAuth, follow the [login guide](../../docs/login.md). In Codex, ask “Use supdb_v2 to get the catalog status.”

Tools work without skills. To package the two optional canonical skills:

```sh
uv run --locked python integrations/codex/build_plugin.py /tmp/suppliermcp-plugin --url https://your-endpoint.example/mcp
```

This builds a portable Agent Plugins 1.0 package. Its JSON manifests are validated against vendored upstream schemas in tests. The package intentionally contains no credentials or token interpolation. Configure bearer authentication separately in the client. Do not enable both plugin MCP wiring and an identical manual MCP entry unless you want duplicate tool registrations. For clients that cannot configure authentication for a portable package, use the TOML connection and copy only the skills into that client's project skill directory.

For the native Codex plugin, add `--codex`. This writes `.codex-plugin/plugin.json`, `.mcp.json`, and the same two skills. The bundled HTTP connection reads `SUPPLIERMCP_THINKHOME_TOKEN` from the Codex process environment; it contains no token. Load your protected token before launching Codex. The native format is validated by the packaging test and by installing it with the Codex CLI.

The GitHub release's Codex archive includes a local marketplace. Extract it, then install from the extracted root:

```sh
codex plugin marketplace add "$PWD"
codex plugin add suppliermcp@thinkhome-suppliermcp
```

Restart an already running desktop client to load the plugin and MCP configuration. To use an existing authenticated connection, such as `mcp_servers.supdb_v2`, instead of supplying an environment variable to the desktop process, disable only the bundled duplicate connection:

```toml
[plugins."suppliermcp@thinkhome-suppliermcp".mcp_servers.suppliermcp]
enabled = false
```

The plugin's skills remain enabled. Keep authentication in the client's protected configuration, never in a release archive or a marketplace manifest. Installation of a local/GitHub package is separate from publication in the public OpenAI plugin directory.

Sources checked 2026-11-05: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Agent Plugins schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json). MCP resources expose identical skill text, but automatic loading of remote skills is not assumed.

For an isolated development server, use `http://127.0.0.1:8000/mcp` with `bearer_token_env_var = "SUPPLIERMCP_TOKEN"`. For the ThinkHome HTTPS server, use a separate credential in `SUPPLIERMCP_THINKHOME_TOKEN`. Keep each client environment file outside Git, load it into the launching process, and renew static tokens before expiry. Each token must match its server's subject grant, issuer and audience.
