---
name: council-plan
description: Produce an approved, reviewable software project plan and roadmap without editing application code.
---

# Council Plan

Actions: `plan-project` creates or revises the plan; `roadmap-add-item` adds one uniquely slugged row with goal, dependencies, acceptance signal, owner, and initial `unstarted` status without rewriting other rows.

Use `repo-explorer`, `system-architect`, and `project-planner`; use `security-adviser` for preimplementation trust-boundary design. One editor writes `.project-files/plan/project-outline.md` and `feature-implementation.md` from their namesake templates, and `roadmap.md` from `templates/project-roadmap.md`. Record lifecycle metadata in `.project-files/plan/project-state.json` per `schemas/project-state.schema.json` and the canonical directory-digest algorithm in `docs/ARTIFACT_CONTRACT.md`. Validate the artifacts and require independent `correctness-reviewer` and `security-reviewer` reports before presenting them for approval. Approval requires approver, UTC time, approved revision, and the canonical artifact-set digest; content changes increment revision and invalidate the old approval. Do not edit application code. Ask the user to approve or choose an item for `$parliament-of-codex:council-scope`.
