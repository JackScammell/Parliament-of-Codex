---
name: council-decisions
description: Create, supersede, and re-evaluate durable architectural decisions using ADRs and structured debate.
---

# Council Decisions

Choose one action: `adr-new`, `adr-supersede`, or `decision-review`.

- `adr-new`: create `.project-files/adrs/NNNN-<slug>.md` with status, context,
  decision, alternatives, consequences, validation signals, and revisit
  triggers. Allocate the next unused four-digit number and update `INDEX.md`.
- `adr-supersede`: preserve the old ADR, change its status to
  `superseded-by-NNNN`, add a dated forward link and rationale, then update
  both the replacement ADR and index.
- `decision-review`: load an ADR, council report, or prior debate; identify its
  assumptions; test them against current evidence; use `$council-debate` for
  material trade-offs; return `HOLD`, `AMEND`, or `SUPERSEDE`. Append the review
  result without rewriting historical rationale.

All decision artifacts stay in `.project-files/` and must surface dissent.
