# Changelog

## 0.3.0

Migration: follow [the 0.2 → 0.3 guide](docs/MIGRATION_0_3.md) before using old
project artifacts with the new topology.

- Breaking: normalized durable artifacts to one lowercase `.project-files/`
  graph with explicit lifecycle/approval and transient `.parliament/` state.
- Hardened Python 3.9+ state tooling against traversal/symlink escapes,
  collisions, unsafe deletion, malformed/unbounded data, ambiguous Git state,
  mixed currencies, and accidental state creation; added retention/clear.
- Made correctness/security gates auditable across every tracked-file workflow;
  added debate, ADR, review report, council report, and review-debt contracts.
- Added trust-boundary/secret-redaction rules and made orchestration read-only.
- Corrected namespaced invocation, installation/configuration guidance, plugin
  metadata, all 66 explicit action contracts, and repository-wide validation.

## 0.2.0

- Added 15 skills, 33 council roles, and initial mappings for 66 legacy actions.
- Added portable local state tooling and initial workflow documentation.

## 0.1.0

- Established the separate Codex plugin foundation.
