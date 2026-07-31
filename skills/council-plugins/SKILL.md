---
name: council-plugins
description: Inspect or install Codex plugins safely through the configured marketplace.
---

# Council Plugins

Choose one action: `plugin-list` or `plugin-install`.

- `plugin-list`: use Codex plugin discovery or `codex plugin list` when the CLI
  is available, then report installed plugins and their capabilities.
- `plugin-install`: inspect source, permissions, MCP tools, hook behavior,
  authentication, and data flows before asking the user to approve installation.
  Never install a plugin merely because it sounds adjacent to the request.
