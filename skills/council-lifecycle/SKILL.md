---
name: council-lifecycle
description: Manage Parliament project status, snapshots, replay, audits, CI watching, and fast-track exceptions.
---

# Council Lifecycle

Choose one action: `project-status`, `session-snapshot`, `debate-replay`,
`docs-audit`, `env-doctor`, `settings-audit`, `ci-watch`, or `fast-track`.

- `project-status`: inspect `.project-files/roadmap/*/tasks.md` and report
  complete, in-progress, scoped, and unstarted items. Use
  `scripts/parliament_state.py project-status` when available.
- `session-snapshot`: create, list, show, or prune a local state snapshot with
  `scripts/parliament_state.py snapshot`. Write a concise council summary
  before creating the snapshot; never capture secrets.
- `debate-replay`: load a recorded decision and re-run `$council-debate` with
  the same question and participants. Compare verdict, dissent, and evidence;
  report best-effort consistency, not deterministic model equivalence.
- `docs-audit`: compare current behavior, commands, and configuration with
  documentation. Report drift and update only verified content.
- `env-doctor`: inspect Git state, required commands, Codex configuration,
  agent files, skills, and local state access. Do not change settings.
- `settings-audit`: review sandbox, approvals, hooks, MCP, secrets exposure,
  and configuration precedence. Recommend least-privilege changes.
- `ci-watch`: inspect the current branch's CI through configured tools or
  available GitHub integration, then summarize terminal status and failures.
- `fast-track`: allow an urgent limited-scope change only after correctness and
  security review. Record skipped optional reviews as explicit review debt in
  `.parliament/` and schedule a normal follow-up review.
