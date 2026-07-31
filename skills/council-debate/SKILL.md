---
name: council-debate
description: Run a bounded, structured Codex debate to make a technical decision with visible disagreement and evidence.
---

# Council Debate

Use this skill for architectural or technical decisions with genuine trade-offs.

1. Define the decision question, constraints, decision owner, and deadline.
2. Ask `repo-explorer` for evidence from the existing project when relevant.
3. Ask `deliberation-conductor` to select two to five relevant advisers from
   `docs/AGENT_SELECTION.md` and collect independent positions in parallel.
4. Run one challenge round only for material disagreements. Participants must
   critique evidence and assumptions, not personalities or preferences.
5. Record the decision in `.project-files/decisions/` using the council report
   template. Include alternatives rejected, dissent, validation signals, and
   a revisit trigger.

Use `INCOMPLETE` when evidence is insufficient or a required security or
correctness perspective is unavailable. Do not edit product code.
