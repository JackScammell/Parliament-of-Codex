# Parliament of Codex

Parliament of Codex 0.3.0 provides 15 qualified skills and 33 project-scoped
agent definitions for inventory-first planning, implementation, review, and
operations. All tracked-file workflows are governed by independent correctness
and security review.

## Start here

- [Installation](docs/INSTALLATION.md) — marketplace installation, upgrade, removal, and source development
- [0.2 → 0.3 migration](docs/MIGRATION_0_3.md) — backup, mapping, collision/orphan handling, validation, and rollback
- [Getting started](docs/GETTING_STARTED.md) — qualified prompts for common workflows
- [Artifact contract](docs/ARTIFACT_CONTRACT.md) — the canonical `.project-files/` and `.parliament/` graph
- [Configuration](docs/CONFIGURATION.md) and [agent selection](docs/AGENT_SELECTION.md)
- [Trust boundaries](docs/TRUST_BOUNDARIES.md)
- [Feature parity](docs/FEATURE_PARITY.md), [state tooling](docs/STATE_TOOLING.md), and [validation](docs/VALIDATION.md)
- [Porting status](docs/PORTING_PLAN.md) and [changelog](CHANGELOG.md)

Installed skills are namespace-qualified:

`$parliament-of-codex:council-core`, `council-plan`, `council-scope`,
`council-implement`, `council-review`, `council-debate`, `council-decisions`,
`council-engineering`, `council-quality`, `council-release`,
`council-operations`, `council-lifecycle`, `council-onboard`,
`council-discovery`, and `council-plugins` (each with the same prefix).

## Repository layout

- `skills/`: distributed workflows and all 66 explicit legacy action aliases
- `.codex/agents/`: 33 project-scoped role definitions; installation does not guarantee their availability in another project
- `templates/` and `schemas/`: human and machine artifact contracts
- `scripts/parliament_state.py`: Python 3.9+ local snapshots, telemetry, metrics, and project status
- `scripts/validate_repository.py` and `tests/`: dependency-free validation

Durable artifacts belong in `.project-files/`. Local telemetry, snapshots, and
disposable evidence belong in ignored/untracked `.parliament/`. Never store
secrets in either location.
