---
name: council-review
description: Review working-tree changes with a governed, relevance-based Codex council.
---

# Council Review

Use this skill for a serious review of local changes.

1. Establish the review range and inventory changed files plus their callers
   and relevant tests.
2. Run `correctness-reviewer` and `security-reviewer` in parallel. Add focused
   reviewers only where the diff warrants it, such as architecture, privacy,
   performance, accessibility, testing, or documentation.
3. Wait for each selected reviewer. A missing security or correctness report
   means the result is `INCOMPLETE`, never approval.
4. Consolidate only actionable findings, ordered by severity. Include file and
   symbol evidence, impact, and a clear recommendation.
5. End with exactly one verdict: `APPROVE`, `CHANGES REQUESTED`, or `INCOMPLETE`.
