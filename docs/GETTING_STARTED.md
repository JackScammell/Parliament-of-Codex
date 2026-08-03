# Getting Started

Follow [installation](INSTALLATION.md), verify `codex plugin list`, and start a
new thread. Plugin installation bundles skills; verify required project-scoped
agents separately as described in [configuration](CONFIGURATION.md).

## Plan, scope, implement, review

```text
Use $parliament-of-codex:council-plan with action plan-project to plan a customer
portal. Inventory reuse, define MVP/non-goals/risks, and write the canonical
.project-files/plan artifacts without editing application code.
```

After recorded approval:

```text
Use $parliament-of-codex:council-scope with action roadmap-item-scope for
user-authentication. Create .project-files/work-items/user-authentication/spec.md,
tasks.md, and lifecycle state with verifiable acceptance criteria.
```

```text
Use $parliament-of-codex:council-implement with action implement-task-list for
the approved user-authentication work item. Use one editor, validate, and wait
for correctness-reviewer and security-reviewer before completion.
```

```text
Use $parliament-of-codex:council-review with action parliament-review to review
HEAD against its base. Persist exact range, findings, validation, and mandatory
reviewer status; be harsh and return one verdict.
```

See [feature parity](FEATURE_PARITY.md) for every action. Commit durable
`.project-files/` artifacts when the project should share them. Keep
`.parliament/` ignored/untracked and free of secrets.
