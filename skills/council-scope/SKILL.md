---
name: council-scope
description: Break an approved roadmap item into a verifiable specification and task list before implementation.
---

# Council Scope

Action `roadmap-item-scope` verifies the approved roadmap revision/digest, inventories reuse with `repo-explorer`, and asks one `scope-weaver` editor to create `.project-files/work-items/<slug>/spec.md` from `templates/work-item-spec.md`, plus `tasks.md` and `project-state.json` from their contracts. Include in/out scope, dependencies, security design from `security-adviser`, validation, rollback, acceptance criteria, and tasks using exactly `unstarted`, `scoped`, `in-progress`, or `complete`. Have `system-architect` review relevant design, validate the artifacts, then require independent `correctness-reviewer` and `security-reviewer` reports. Any content change invalidates approval. Do not implement product code; point to `$parliament-of-codex:council-implement`.
