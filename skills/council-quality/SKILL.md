---
name: council-quality
description: Improve test confidence, accessibility, internationalisation, and technical-debt visibility through focused council review.
---

# Council Quality

Choose one action: `coverage-audit`, `generate-tests`, `mutation-test`,
`test-health`, `track-debt`, or `i18n-audit`.

- `coverage-audit`: prioritize uncovered behavior by risk, not a percentage.
- `generate-tests`: follow project test conventions and cover normal, failure,
  boundary, and regression behavior.
- `mutation-test`: use available mutation tooling or reasoned candidate changes
  to identify weak assertions; never leave mutations applied.
- `test-health`: identify flakes, time dependence, ordering coupling, network
  reliance, stale assertions, and non-deterministic fixtures.
- `track-debt`: inventory TODO/FIXME/HACK markers plus complexity, duplication,
  dependency, and test risks; rank by impact and effort.
- `i18n-audit`: use `i18n-reviewer` to examine localisable text, pluralisation,
  locale formats, and translation-safe interfaces.

Return evidence, impact, recommended next action, and a clear distinction
between confirmed problems and opportunities.
