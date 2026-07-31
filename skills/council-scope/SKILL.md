---
name: council-scope
description: Break an approved roadmap item into a verifiable specification and task list before implementation.
---

# Council Scope

Use this skill after a project plan exists and one roadmap item needs detailed
implementation scope.

1. Confirm the selected roadmap item and read its dependencies.
2. Ask `repo-explorer` to identify existing code, tests, APIs, and conventions
   that the item must reuse or extend.
3. Ask `scope-weaver` to produce `Spec.md` and `tasks.md` under
   `.project-files/roadmap/<item-slug>/` using the templates.
4. Include a test strategy, rollout or rollback requirements when relevant,
   and a definition of done for every task.
5. Ask `system-architect` and `security-reviewer` to review only the parts
   relevant to their domains. Update the scope or record accepted trade-offs.

Do not implement product code in this skill. End with the next task to execute.
