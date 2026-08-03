---
name: council-decisions
description: Create, supersede, and re-evaluate durable architectural decisions using ADRs and structured debate.
---

# Council Decisions

Use `templates/architectural-decision.md` under `.project-files/decisions/adrs/`.

- `adr-new`: allocate `NNNN-<slug>.md`, capture status/revision, context, constraints, owner and approval evidence, decision, alternatives, dissent, consequences, security/privacy, validation, and revisit triggers; update `index.md`.
- `adr-supersede`: preserve history, set old status `superseded`, add dated bidirectional links and rationale, and update `index.md`.
- `decision-review`: test assumptions against current evidence; invoke `$parliament-of-codex:council-debate` for material trade-offs and append `HOLD`, `AMEND`, or `SUPERSEDE` without rewriting history.

Only `proposed`, `accepted`, `deprecated`, and `superseded` are valid statuses. Content changes increment revision and invalidate stale approval digests.
One editor owns ADR/index mutations. Validate links and lifecycle fields, then require independent `correctness-reviewer` and `security-reviewer` review before completion.
