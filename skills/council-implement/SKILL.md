---
name: council-implement
description: Implement an approved scoped task with inventory-first analysis and mandatory correctness and security review.
---

# Council Implement

Use this skill only for an approved task in `.project-files/roadmap/`.

1. Read the task, its specification, dependencies, and prior council reports.
2. Ask `repo-explorer` to refresh the inventory and reuse decision. If the
   scope no longer fits the repository, stop and propose a scoped-plan update.
3. Assign `implementation-owner` as the sole editor unless work is safely
   partitioned into disjoint files or worktrees.
4. Require focused validation for the changed behavior.
5. Run `correctness-reviewer` and `security-reviewer` on the diff. Add
   `testing-reviewer` when tests change or risk is non-trivial.
6. Address accepted findings, rerun affected validation, and write a council
   report from `templates/council-report.md`.

Never return `APPROVE` if a required reviewer did not report. Mark completed
tasks in the task list only after validation and review are recorded.
