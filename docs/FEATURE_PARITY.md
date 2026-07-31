# Feature Parity Map

Every active Parliament of Chaos command has a Codex-native skill and action.
Codex groups related actions into focused skills instead of recreating Claude
slash-command files one-for-one.

| Claude command | Codex skill and action |
| --- | --- |
| `ask-council`, `summon-council`, `summon-specialist` | `$council-core` |
| `summon-grumpy-reviewer`, `parliament-review` | `$council-review` |
| `plan-project`, `roadmap-add-item` | `$council-plan` |
| `roadmap-item-scope` | `$council-scope` |
| `implement-task-list` | `$council-implement` |
| `project-status` | `$council-lifecycle project-status` |
| `debate-topic`, `debate-analytics` | `$council-debate` |
| `debate-replay` | `$council-lifecycle debate-replay` |
| `adr-new`, `adr-supersede`, `decision-review` | `$council-decisions` |
| `pre-commit-check`, `commit-and-push`, `format-code`, `lint-fix` | `$council-engineering` |
| `run-tests`, `security-scan`, `clean-imports`, `update-dependencies` | `$council-engineering` |
| `dead-code-sweep`, `update-docs`, `analyse-queries`, `git-workflow`, `scaffold` | `$council-engineering` |
| `coverage-audit`, `generate-tests`, `mutation-test` | `$council-quality` |
| `test-health`, `track-debt`, `i18n-audit` | `$council-quality` |
| `cut-release`, `release-notes-draft`, `plugin-upgrade` | `$council-release` |
| `telemetry-query`, `parliament-metrics`, `cost-report`, `agent-usage-stats` | `$council-operations` |
| `incident`, `infra-review`, `parliament-loop`, `parliament-monitor` | `$council-operations` |
| `parliament-optimize`, `parliament-webhook`, `changelog-review`, `retro` | `$council-operations` |
| `session-snapshot`, `docs-audit`, `settings-audit`, `env-doctor` | `$council-lifecycle` |
| `fast-track`, `ci-watch`, `parliament-doctor` | `$council-lifecycle` |
| `onboard-codebase` | `$council-onboard` |
| `list-agents`, `explain-agent`, `list-commands`, `version`, `readme`, `changelog` | `$council-discovery` |
| `plugin-install`, `plugin-list` | `$council-plugins` |

## Runtime differences

Codex does not expose the same Claude hook events or plugin-data variables.
This port stores portable state locally under `.parliament/`, delegates through
Codex subagents, and uses Codex-supported automation or MCP only after it is
explicitly configured. Replay is evidence comparison, not a claim that language
model output is deterministic.
