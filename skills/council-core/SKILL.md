---
name: council-core
description: Coordinate Codex specialists to inventory, plan, implement, or answer cross-cutting software questions with governed review.
---

# Council Core

Use this skill when a task spans multiple technical domains or needs a second
opinion before code changes.

## Workflow

1. Classify the request as `answer`, `plan`, or `implement`. Ask only if the
   intended mode changes the outcome materially.
2. Ask `repo-explorer` to inventory relevant code, tests, and reuse candidates.
3. Select only the specialists needed by the evidence. Use parallel subagents
   for independent, read-heavy investigation and request concise reports.
4. In `plan` mode, write an approved plan to `.project-files/plans/`; do not
   edit application code.
5. In `implement` mode, choose one implementation owner after analysis. Require
   `correctness-reviewer` and `security-reviewer` to review the resulting diff.
6. Resolve findings in governance priority order. Re-run focused validation and
   report approval, remaining trade-offs, or `INCOMPLETE` if a floor report is
   unavailable.

## Output

Return: inventory and reuse decision; selected roles; conclusion or plan;
implemented files and validation; reviewer verdicts; deferred work and open
trade-offs.
