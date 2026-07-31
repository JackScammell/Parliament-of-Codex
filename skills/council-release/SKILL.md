---
name: council-release
description: Prepare releases, draft release notes, and safely update Parliament plugin versions.
---

# Council Release

Choose one action: `cut-release`, `release-notes-draft`, or `plugin-upgrade`.

- `cut-release`: verify clean state, version policy, changelog, tests, build,
  compatibility, release notes, rollback plan, and tag target. Present the
  exact release commands for approval before running them.
- `release-notes-draft`: derive user-visible changes, migration notes, fixes,
  risks, and acknowledgements from Git history and merged work; avoid claiming
  behavior that is not evidenced.
- `plugin-upgrade`: update plugin version-bearing files together, validate the
  manifest, refresh local marketplace cache state when installed, and require a
  new Codex thread for plugin retesting.
