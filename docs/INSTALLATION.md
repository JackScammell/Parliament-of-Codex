# Installation

Upgrading a project from 0.2 also requires the explicit [0.3 artifact/state
migration](MIGRATION_0_3.md); reinstalling the plugin does not move project data.

Installation writes user-level Codex marketplace/plugin state; run these
commands yourself after reviewing the source.

## Personal local marketplace

Create `~/.agents/plugins/marketplace.json` for a personal list (or
`<target-repo>/.agents/plugins/marketplace.json` for a repo-scoped list). Its
`plugins[]` entry must use a `./`-prefixed `source.path` relative to that
marketplace root and point to this plugin folder. Restart the desktop app to
discover a directly configured personal/repo list, or register the marketplace
root in the CLI and install using the marketplace name it reports:

```bash
codex plugin marketplace add /absolute/path/to/marketplace
codex plugin marketplace list
codex plugin add parliament-of-codex@<marketplace-name>
codex plugin list
```

For a non-default local marketplace, always include
`@<marketplace-name>` when installing so the source is unambiguous. Start a new
Codex thread and invoke a qualified skill such as
`$parliament-of-codex:council-review`.

For a Git-backed marketplace, refresh its catalog. To force replacement of an
installed local version, remove it, add it again, and start a new session:

```bash
codex plugin marketplace upgrade <marketplace-name>
codex plugin remove parliament-of-codex@<marketplace-name>
codex plugin add parliament-of-codex@<marketplace-name>
codex plugin list
```

To remove it:

```bash
codex plugin remove parliament-of-codex@<marketplace-name>
codex plugin marketplace remove <marketplace-name>
```

The interactive CLI alternative is `/plugins`, where marketplace tabs expose
install, enable/disable, and uninstall controls. Check `codex plugin --help`
before mutating user configuration. This repository's validation does not
register, reinstall, update, or remove user-level plugin/cache state.

## Source development

Opening this checkout applies its `AGENTS.md`, `.codex/config.toml`, and local
agent definitions for repository development. That is not plugin installation.
To exercise source skills without installation, explicitly ask Codex to read the
relevant `skills/<name>/SKILL.md`. Re-run repository validation after edits.
