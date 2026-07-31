---
name: council-engineering
description: Execute everyday engineering workflows for tests, linting, security, dependencies, Git, documentation, and scaffolding.
---

# Council Engineering

Choose one action: `pre-commit-check`, `commit-and-push`, `format-code`,
`lint-fix`, `run-tests`, `security-scan`, `clean-imports`,
`update-dependencies`, `dead-code-sweep`, `update-docs`, `analyse-queries`,
`git-workflow`, or `scaffold`.

First inventory the repository's documented scripts and established conventions.

- `pre-commit-check`: detect and run the relevant formatter, linter, typecheck,
  tests, build, and secret scan; distinguish failures from unavailable tools.
- `commit-and-push`: summarize the intended diff, run pre-flight checks, propose
  a commit message and exact Git commands; do not commit or push without the
  user's explicit request.
- `format-code`, `lint-fix`, `clean-imports`: run only detected project tools,
  review the diff, and avoid unrelated rewrites.
- `run-tests`: select focused tests first, then broader validation when useful;
  explain failures and do not mask flakes.
- `security-scan`: inspect dependencies, secrets, unsafe patterns, inputs, and
  configuration; use `security-reviewer` for findings requiring judgment.
- `update-dependencies`: identify compatibility and security rationale, review
  changelogs, make one coherent update set, and validate it.
- `dead-code-sweep`, `analyse-queries`: return evidence before removal or query
  changes; require tests and migration/rollback strategy where appropriate.
- `update-docs`, `scaffold`: follow existing conventions and only document or
  generate verified behavior.
- `git-workflow`: explain merge, rebase, cherry-pick, bisect, or conflict steps
  before executing potentially destructive Git operations.
