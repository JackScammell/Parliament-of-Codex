# Agent Selection

Use the smallest council that can assess the task. Every code-changing council
workflow includes `correctness-reviewer` and `security-reviewer`.

| Signal in the task or diff | Add these agents |
| --- | --- |
| New system boundary, major trade-off, service split | `system-architect`, `architecture-reviewer` |
| API or client contract | `api-specialist` |
| Database schema, query, migration, retention | `data-specialist` |
| Data, configuration, or API migration | `migration-specialist` |
| Backend concurrency, caching, I/O, recovery | `backend-specialist`, `resilience-specialist` |
| User interface or interaction | `ui-ux-specialist`, `accessibility-reviewer` |
| CI, deployment, infrastructure, release | `pipeline-specialist`, `cost-reviewer` |
| New dependency or version change | `dependency-specialist` |
| Configuration, environments, flags, secrets | `config-specialist` |
| Logging, metrics, tracing, alerts | `observability-specialist` |
| Personal data or regulated data | `privacy-reviewer` |
| Threat model or secure design before implementation | `security-adviser` |
| Refactor or accumulating complexity | `refactor-specialist`, `maintainability-reviewer` |
| Latency, capacity, memory, throughput | `performance-reviewer` |
| Tests added, changed, or missing | `testing-reviewer` |
| Public behavior or setup changes | `documentation-reviewer` |
| New or changed developer/user documentation | `documentation-specialist` |
| Localisable user-facing content | `i18n-reviewer` |
| Versioning, changelog, or release decision | `release-specialist` |
| Project conventions or compatibility standards | `standards-reviewer` |

## Review outcomes

- `APPROVE`: mandatory reviewers reported and no unresolved blocking issue remains.
- `CHANGES REQUESTED`: a concrete finding needs resolution before acceptance.
- `INCOMPLETE`: evidence or a required reviewer report is missing.

## Original council mapping

This project retains the original council's domains while using Codex-native,
descriptive names. For example, `backend-specialist` corresponds to the backend
role, `data-specialist` to database expertise, and `security-reviewer` to the
security review floor. The functional role matters more than copying a Claude
persona name verbatim.
