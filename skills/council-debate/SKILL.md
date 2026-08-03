---
name: council-debate
description: Run a bounded, structured Codex debate to make a technical decision with visible disagreement and evidence.
---

# Council Debate

Actions: `debate-topic` runs a decision debate; `debate-analytics` summarizes recorded participant positions, evidence coverage, agreement/disagreement, dissent, and revisit signals across selected debate records without inventing quantitative confidence.

Define question, constraints, owner, and UTC deadline. Ask `repo-explorer` for project evidence and `deliberation-conductor` for two to five relevant independent positions. Run one evidence-focused challenge round. One editor writes `.project-files/decisions/debates/<slug>.md` (and optional same-basename JSON) using `templates/debate-record.md` and `schemas/debate-record.schema.json`, including participants, positions, evidence, decision, alternatives, dissent, validation, revisit trigger, and replay link. Validate it and require independent `correctness-reviewer` and `security-reviewer` review before recording completion. Do not edit product code; insufficient required evidence yields `INCOMPLETE`.
