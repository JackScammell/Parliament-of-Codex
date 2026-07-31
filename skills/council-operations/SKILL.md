---
name: council-operations
description: Operate Parliament with incident, infrastructure, monitoring, telemetry, cost, retrospective, and change-analysis workflows.
---

# Council Operations

Choose one action: `telemetry-query`, `parliament-metrics`, `cost-report`,
`agent-usage-stats`, `incident`, `infra-review`, `parliament-loop`,
`parliament-monitor`, `parliament-optimize`, `parliament-webhook`,
`changelog-review`, or `retro`.

- `telemetry-query`, `parliament-metrics`, `cost-report`, `agent-usage-stats`:
  use `scripts/parliament_state.py telemetry` and `metrics` when available.
  Report only locally recorded data; mark unavailable cost or token fields.
- `incident`: establish impact, owner, timeline, hypotheses, containment,
  evidence, communications, recovery validation, and a blameless follow-up.
- `infra-review`: use `pipeline-specialist`, `security-reviewer`, and
  `cost-reviewer` to inspect infrastructure definitions, deployment, secrets,
  least privilege, resilience, and rollback.
- `parliament-loop` and `parliament-monitor`: design recurring checks or
  monitors using Codex-supported automation only. Do not claim an automation is
  scheduled until the user has configured it.
- `parliament-optimize`: assess role selection, concurrency, review coverage,
  and state volume against observed workload; keep the mandatory review floor.
- `parliament-webhook`: use a controlled MCP or explicit user-approved command
  for external notifications; do not store endpoint secrets in Git.
- `changelog-review` and `retro`: extract actionable changes, risks, hotspots,
  churn, and follow-ups from verified history and current evidence.
