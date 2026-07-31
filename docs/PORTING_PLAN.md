# Codex Porting Plan

## Goal

Create a separate Codex-native project that preserves the useful behavior of
Parliament of Chaos without adding Codex files or runtime dependencies to the
Claude Code repository.

## Compatibility map

| Claude capability | Codex-native replacement | Status |
| --- | --- | --- |
| Markdown agents and `Task()` fan-out | `.codex/agents/*.toml` and explicit parallel subagents | Initial role coverage created |
| Rules loaded by Claude hooks | Root `AGENTS.md` and skill instructions | Foundation created |
| Slash-command workflows | Skills invoked with `$name` | Six core workflows created |
| Read-only grumpy reviewers | Read-only custom reviewer agents | Initial domain reviewer fleet created |
| `.project-files/` plans and specs | Same project-owned artifact location | Preserved |
| `${CLAUDE_PLUGIN_DATA}` telemetry | Gitignored `.parliament/` state | Implemented as portable local state tooling |
| Claude lifecycle hooks | Codex hook equivalents after event-by-event audit | Ported as explicit lifecycle workflows |
| Python deliberation library | Optional Codex CLI/MCP sidecar or OpenAI API adapter | Native Codex debate is the default; integration remains optional |

## Delivery phases

## Completed port

- 33 Codex-native council roles cover orchestration, planning, specialist
  analysis, and read-only review.
- Fifteen skills cover every active Claude command through focused actions.
- Project artifacts, ADRs, onboarding, engineering, quality, release,
  operations, discovery, lifecycle, and plugin workflows are available.
- Portable local snapshots, telemetry, metrics, and project status replace the
  Claude-specific plugin-data dependency.

## Optional future extensions

- Connect external services through purpose-built MCP servers.
- Configure Codex automations or hooks where the local environment supports
  them.
- Add an API-backed Python deliberation sidecar only if native Codex debate
  proves insufficient in measured use.

## Acceptance criteria

- A user can install or open this repository without touching Parliament of
  Chaos.
- A council task inventories existing code before proposing new work.
- Implementation tasks receive security and correctness review from read-only
  agents.
- Plans and review reports are reproducible project artifacts.
- The source Claude repository remains independent and unchanged.
