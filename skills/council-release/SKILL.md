---
name: council-release
description: Prepare releases, draft release notes, and safely update Parliament plugin versions.
---

# Council Release

- `cut-release`: verify state, version policy, changelog, tests/build, compatibility, notes, rollback, and tag target; require user approval before publishing/tagging.
- `release-notes-draft`: derive claims and migration notes from verified history.
- `plugin-upgrade`: update all repository version-bearing files, validate, and require a new thread for installed-plugin retest; user-level marketplace/cache changes require explicit user authorization and are never implied.

Inspect hooks and package lifecycle side effects, use least privilege, and redact secrets. Any tracked-file mutation uses one `implementation-owner`, focused validation, and mandatory independent `correctness-reviewer` and `security-reviewer` review before completion.
