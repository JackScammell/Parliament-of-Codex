# Parliament Governance

## Council workflow

For cross-cutting planning, implementation, or review tasks, use the council
skills and delegate independent read-heavy work to focused subagents. Start
with an inventory of relevant code, tests, and existing helpers. Prefer
extending verified capabilities over creating replacements.

The coordinator synthesises returned reports and records material disagreement.
It must not present unresolved security or correctness concerns as approval.

## Review floor

Every code-changing council workflow includes a correctness review and a
security review. Add testing, architecture, privacy, accessibility,
performance, documentation, and cost reviewers only when the change makes
their domain relevant. Reviewers do not edit files or run write-capable tools.

## Conflict priority

Resolve conflicts in this order: security, correctness, maintainability,
performance, then convenience. Keep genuine trade-offs visible to the user.

## State and artifacts

Store plans, ADRs, specifications, and task lists in `.project-files/`.
Store transient council telemetry, snapshots, and review evidence in
`.parliament/`, which is ignored by Git. Do not store secrets in either path.

## Implementation discipline

Parallel write-capable agents can conflict. Use parallelism for investigation
and review; coordinate implementation serially unless worktrees or disjoint
file ownership make parallel edits safe. Validate the changed behavior before
reporting completion.
