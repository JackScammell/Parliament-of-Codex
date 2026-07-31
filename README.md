# Parliament of Codex

A Codex-native successor to Parliament of Chaos. It retains a 33-role council
of governed specialist and review workflows without modifying the Claude Code
project it was inspired by.

## Current scope

The first release provides reusable council skills, governed review, and
project-scoped Codex agents. It intentionally prioritises planning, scoping,
implementation coordination, and review before porting the long tail of
workflow commands.

## Develop it locally

1. Open this repository in Codex.
2. The local `AGENTS.md` and `.codex/agents/` files apply while developing this
   project.
3. Before the plugin is registered in a local marketplace, ask Codex to read a
   workflow file directly, for example `skills/council-plan/SKILL.md`.

## Install for reuse

Bundled skills become `$council-plan`, `$council-scope`, `$council-implement`,
`$council-core`, `$council-review`, and `$council-debate` after the plugin is
registered and installed from a local marketplace. Marketplace registration is
kept as an explicit, separate step because it writes to your user-level Codex
configuration. Once installed, start a new Codex thread before testing a skill.

Keep project-specific decisions and plans in `.project-files/`.

See `docs/GETTING_STARTED.md` for example prompts and `docs/VALIDATION.md` for
local repository checks.

## Repository layout

- `.codex/agents/` contains the Codex-native council roles.
- `skills/` contains reusable workflows distributed by the plugin.
- `templates/` and `schemas/` standardise project and council artifacts.
- `AGENTS.md` defines governance that applies to every task.
- `docs/PORTING_PLAN.md` records the staged migration and compatibility map.

## Principles

- Inventory existing code before proposing new abstractions.
- Use parallel agents for independent, read-heavy work.
- Keep reviewers read-only and require security and correctness review floors.
- Keep user-facing artifacts in the project and transient state in `.parliament/`.
