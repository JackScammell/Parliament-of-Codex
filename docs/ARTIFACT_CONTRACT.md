# Artifact Contract

Parliament 0.3.0 uses one lowercase, project-owned artifact graph:

```text
.project-files/
  plan/{project-outline.md,feature-implementation.md,roadmap.md,project-state.json}
  work-items/<slug>/{spec.md,tasks.md,project-state.json}
  reports/{council,reviews}/
  decisions/{debates,adrs}/
  review-debt/
.parliament/
  snapshots/
  evidence/
  activity.jsonl
```

`.project-files/` is durable, reviewable, and normally committed. `.parliament/`
is local, transient, ignored, untracked, and never a substitute for an auditable
report. Only disposable raw excerpts belong in `.parliament/evidence/`.

## Lifecycle and approval

Plan and work-item directories use `project-state.json` conforming to
`schemas/project-state.schema.json`. States are `draft`, `in-review`,
`approved`, `invalidated`, and `superseded`. Start at revision 1 and increment
revision whenever governed content changes. Approval records the human or
authorized approver, UTC time, approved revision, and SHA-256 of the approved
artifact set. Compute a directory digest by sorting governed relative paths and
hashing each UTF-8 path, a NUL byte, its exact file bytes, and a final NUL byte
in that order; exclude `project-state.json` itself. A changed digest/revision, changed dependency, superseding
decision, or material repository drift invalidates approval; record the UTC
time and reason, then obtain fresh approval before implementation.

Task statuses are exactly `unstarted`, `scoped`, `in-progress`, and `complete`.
They describe execution progress and do not replace artifact approval.

## Reports and consumers

JSON files conform to schemas for machine validation; same-basename Markdown
files use templates for human review. `$parliament-of-codex:council-review`
consumes review reports; council-core/implement consume council reports;
council-debate consumes debate records; council-decisions consumes ADRs;
lifecycle fast-track consumes review debt; state tooling consumes snapshot and
telemetry schemas. Every template and schema has one of these consumers.
