# Getting Started

## Before installation

While developing this repository, ask Codex to read a skill file directly. For
example: `Read skills/council-plan/SKILL.md and follow it for this task.`

After this plugin is registered and installed in a local Codex marketplace, use
the `$council-*` names below in a new Codex thread.

## Planning a project

Open a target project in Codex and use:

```text
Use $council-plan to plan a customer portal. Inventory the existing repository,
define an MVP, list non-goals and risks, then write the project artifacts under
.project-files/. Do not edit application code.
```

Review and approve the generated project outline and roadmap before scoping an
item.

## Scoping a roadmap item

```text
Use $council-scope for the `user-authentication` roadmap item. Reuse existing
patterns, create a detailed specification and independently verifiable task
list, then identify the first task to implement.
```

## Implementing safely

```text
Use $council-implement for Task 1 of `user-authentication`. Make only the
approved changes, run focused validation, and require correctness and security
review before marking the task complete.
```

## Reviewing a working tree

```text
Use $council-review to review the current working tree against HEAD. Wait for
correctness and security reviewers, add testing review if relevant, and return
only actionable findings with an explicit verdict.
```

## State ownership

Commit `.project-files/` when its plans, specifications, and ADRs should be
shared with the project. Do not commit `.parliament/`; it is local runtime
evidence and telemetry.
