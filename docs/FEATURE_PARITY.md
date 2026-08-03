# Feature Parity Map

All 66 legacy action aliases below have an explicit contract in the named
qualified skill. “Supported” means the workflow contract is structurally
declared and repository validation confirms its mapping; it does not claim 66
end-to-end behavioral tests. External tools still require configuration and
authority.

| Legacy action | Qualified skill | Explicit action | Status |
| --- | --- | --- | --- |
| `ask-council` | `$parliament-of-codex:council-core` | `ask-council` | Supported |
| `summon-council` | `$parliament-of-codex:council-core` | `summon-council` | Supported |
| `summon-specialist` | `$parliament-of-codex:council-core` | `summon-specialist` | Supported |
| `summon-grumpy-reviewer` | `$parliament-of-codex:council-review` | `summon-grumpy-reviewer` | Supported |
| `parliament-review` | `$parliament-of-codex:council-review` | `parliament-review` | Supported |
| `plan-project` | `$parliament-of-codex:council-plan` | `plan-project` | Supported |
| `roadmap-add-item` | `$parliament-of-codex:council-plan` | `roadmap-add-item` | Supported |
| `roadmap-item-scope` | `$parliament-of-codex:council-scope` | `roadmap-item-scope` | Supported |
| `implement-task-list` | `$parliament-of-codex:council-implement` | `implement-task-list` | Supported |
| `project-status` | `$parliament-of-codex:council-lifecycle` | `project-status` | Supported |
| `session-snapshot` | `$parliament-of-codex:council-lifecycle` | `session-snapshot` | Supported |
| `debate-replay` | `$parliament-of-codex:council-lifecycle` | `debate-replay` | Supported |
| `docs-audit` | `$parliament-of-codex:council-lifecycle` | `docs-audit` | Supported |
| `env-doctor` | `$parliament-of-codex:council-lifecycle` | `env-doctor` | Supported |
| `settings-audit` | `$parliament-of-codex:council-lifecycle` | `settings-audit` | Supported |
| `ci-watch` | `$parliament-of-codex:council-lifecycle` | `ci-watch` | Supported |
| `fast-track` | `$parliament-of-codex:council-lifecycle` | `fast-track` | Supported |
| `parliament-doctor` | `$parliament-of-codex:council-lifecycle` | `parliament-doctor` | Supported |
| `debate-topic` | `$parliament-of-codex:council-debate` | `debate-topic` | Supported |
| `debate-analytics` | `$parliament-of-codex:council-debate` | `debate-analytics` | Supported |
| `adr-new` | `$parliament-of-codex:council-decisions` | `adr-new` | Supported |
| `adr-supersede` | `$parliament-of-codex:council-decisions` | `adr-supersede` | Supported |
| `decision-review` | `$parliament-of-codex:council-decisions` | `decision-review` | Supported |
| `pre-commit-check` | `$parliament-of-codex:council-engineering` | `pre-commit-check` | Supported |
| `commit-and-push` | `$parliament-of-codex:council-engineering` | `commit-and-push` | Supported |
| `format-code` | `$parliament-of-codex:council-engineering` | `format-code` | Supported |
| `lint-fix` | `$parliament-of-codex:council-engineering` | `lint-fix` | Supported |
| `run-tests` | `$parliament-of-codex:council-engineering` | `run-tests` | Supported |
| `security-scan` | `$parliament-of-codex:council-engineering` | `security-scan` | Supported |
| `clean-imports` | `$parliament-of-codex:council-engineering` | `clean-imports` | Supported |
| `update-dependencies` | `$parliament-of-codex:council-engineering` | `update-dependencies` | Supported |
| `dead-code-sweep` | `$parliament-of-codex:council-engineering` | `dead-code-sweep` | Supported |
| `update-docs` | `$parliament-of-codex:council-engineering` | `update-docs` | Supported |
| `analyse-queries` | `$parliament-of-codex:council-engineering` | `analyse-queries` | Supported |
| `git-workflow` | `$parliament-of-codex:council-engineering` | `git-workflow` | Supported |
| `scaffold` | `$parliament-of-codex:council-engineering` | `scaffold` | Supported |
| `coverage-audit` | `$parliament-of-codex:council-quality` | `coverage-audit` | Supported |
| `generate-tests` | `$parliament-of-codex:council-quality` | `generate-tests` | Supported |
| `mutation-test` | `$parliament-of-codex:council-quality` | `mutation-test` | Supported |
| `test-health` | `$parliament-of-codex:council-quality` | `test-health` | Supported |
| `track-debt` | `$parliament-of-codex:council-quality` | `track-debt` | Supported |
| `i18n-audit` | `$parliament-of-codex:council-quality` | `i18n-audit` | Supported |
| `cut-release` | `$parliament-of-codex:council-release` | `cut-release` | Supported |
| `release-notes-draft` | `$parliament-of-codex:council-release` | `release-notes-draft` | Supported |
| `plugin-upgrade` | `$parliament-of-codex:council-release` | `plugin-upgrade` | Supported |
| `telemetry-query` | `$parliament-of-codex:council-operations` | `telemetry-query` | Supported |
| `parliament-metrics` | `$parliament-of-codex:council-operations` | `parliament-metrics` | Supported |
| `cost-report` | `$parliament-of-codex:council-operations` | `cost-report` | Supported |
| `agent-usage-stats` | `$parliament-of-codex:council-operations` | `agent-usage-stats` | Supported |
| `incident` | `$parliament-of-codex:council-operations` | `incident` | Supported |
| `infra-review` | `$parliament-of-codex:council-operations` | `infra-review` | Supported |
| `parliament-loop` | `$parliament-of-codex:council-operations` | `parliament-loop` | Supported |
| `parliament-monitor` | `$parliament-of-codex:council-operations` | `parliament-monitor` | Supported |
| `parliament-optimize` | `$parliament-of-codex:council-operations` | `parliament-optimize` | Supported |
| `parliament-webhook` | `$parliament-of-codex:council-operations` | `parliament-webhook` | Supported |
| `changelog-review` | `$parliament-of-codex:council-operations` | `changelog-review` | Supported |
| `retro` | `$parliament-of-codex:council-operations` | `retro` | Supported |
| `onboard-codebase` | `$parliament-of-codex:council-onboard` | `onboard-codebase` | Supported |
| `list-agents` | `$parliament-of-codex:council-discovery` | `list-agents` | Supported |
| `explain-agent` | `$parliament-of-codex:council-discovery` | `explain-agent` | Supported |
| `list-commands` | `$parliament-of-codex:council-discovery` | `list-commands` | Supported |
| `version` | `$parliament-of-codex:council-discovery` | `version` | Supported |
| `readme` | `$parliament-of-codex:council-discovery` | `readme` | Supported |
| `changelog` | `$parliament-of-codex:council-discovery` | `changelog` | Supported |
| `plugin-install` | `$parliament-of-codex:council-plugins` | `plugin-install` | Supported |
| `plugin-list` | `$parliament-of-codex:council-plugins` | `plugin-list` | Supported |

Codex-native replay is evidence comparison, not deterministic reproduction;
automation, CI, webhooks, and marketplaces operate only when configured.
