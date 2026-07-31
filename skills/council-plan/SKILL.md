---
name: council-plan
description: Produce an approved, reviewable software project plan and roadmap without editing application code.
---

# Council Plan

Use this skill for a new project, substantial feature, migration, or decision
that needs a written plan before implementation.

1. Delegate the codebase inventory to `repo-explorer` when a repository exists.
2. Delegate system constraints and alternatives to `system-architect`; include
   `security-reviewer` when data, identity, external input, or permissions are
   involved.
3. Have `project-planner` synthesize the evidence. Keep only necessary
   requirements and state explicit non-goals.
4. Write these artifacts from `templates/` under `.project-files/`:
   `project-outline.md`, `feature-implementation.md`, and `Roadmap.md`.
5. Review the plan with the architecture and security participants. Record
   unresolved trade-offs rather than hiding them.

Do not edit application code. End by asking the user to approve the scope or
select the first roadmap item to detail.
