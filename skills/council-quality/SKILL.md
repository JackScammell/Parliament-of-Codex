---
name: council-quality
description: Improve test confidence, accessibility, internationalisation, and technical-debt visibility through focused council review.
---

# Council Quality

- `coverage-audit`: rank uncovered behavior by risk.
- `generate-tests`: cover normal, failure, boundary, and regression paths using project conventions.
- `mutation-test`: use detected tooling or reasoned candidates and never leave mutations applied.
- `test-health`: find flakes, time/order/network coupling, stale assertions, and nondeterministic fixtures.
- `track-debt`: rank TODO/FIXME/HACK, complexity, duplication, dependency, and test risk by impact/effort.
- `i18n-audit`: use `i18n-reviewer` for localisable text, plurals, locale formats, and translation safety.

Return evidence and distinguish defects from opportunities. When an action changes tracked files, a single `implementation-owner` edits, validation runs, and independent `correctness-reviewer` and `security-reviewer` reports gate completion.
