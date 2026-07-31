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
| `${CLAUDE_PLUGIN_DATA}` telemetry | Gitignored `.parliament/` state | Defined; not implemented |
| Claude lifecycle hooks | Codex hook equivalents after event-by-event audit | Deferred |
| Python deliberation library | Optional Codex CLI/MCP sidecar or OpenAI API adapter | Deferred |

## Delivery phases

### Phase 1: Foundation

- Validate the plugin, root guidance, initial agent set, and core skills.
- Test an end-to-end plan and a governed code review in a sample repository.
- Define a stable JSON schema for council reports and review evidence.

### Phase 2: Council parity

- Port the remaining planning, specialist, and reviewer roles.
- Add planning, scoping, implementation, onboarding, debate, and ADR skills.
- Add reviewer selection rules for privacy, accessibility, performance, tests,
  docs, and cost.

### Phase 3: State and operations

- Implement snapshots, replayable council reports, JSONL telemetry, metrics,
  cost estimates, and project status.
- Map only semantically compatible Codex hook events; do not copy Claude event
  names or plugin-data assumptions.

### Phase 4: Secondary workflows

- Port developer workflow, quality, release, discovery, and operations skills
  according to usage value.
- Add optional integrations through MCP only when a workflow needs controlled
  external state or actions.

### Phase 5: Deliberation engine decision

- Compare native Codex council output with the Python library's structured
  voting, convergence, and analytics features.
- Implement an OpenAI-backed adapter or local MCP/CLI sidecar only if it adds
  measurable value. The current Python model caller is not usable as-is.

## Acceptance criteria

- A user can install or open this repository without touching Parliament of
  Chaos.
- A council task inventories existing code before proposing new work.
- Implementation tasks receive security and correctness review from read-only
  agents.
- Plans and review reports are reproducible project artifacts.
- The source Claude repository remains independent and unchanged.
