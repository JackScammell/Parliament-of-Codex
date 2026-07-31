# State Tooling

`scripts/parliament_state.py` is a dependency-free local utility for project
state that Codex workflows can use when the repository is available locally.
It writes only to `.parliament/`, which is ignored by Git.

## Snapshot

```bash
python3 scripts/parliament_state.py snapshot create \
  --label "before migration" --summary "Approved staged migration plan"
python3 scripts/parliament_state.py snapshot list
python3 scripts/parliament_state.py snapshot prune --keep 20
```

Snapshots capture a user-provided summary, current path, and best-effort Git
metadata. They cannot read or restore private Codex conversation state.

## Telemetry and metrics

```bash
python3 scripts/parliament_state.py telemetry record \
  --event CouncilCompleted --agent council-orchestrator \
  --outcome APPROVE --duration-ms 42000 --tokens 1200
python3 scripts/parliament_state.py telemetry query --since 7d --group-by agent
python3 scripts/parliament_state.py metrics --window 30d --by agent
```

Telemetry is local and opt-in. Cost is only reportable when you record an
explicit cost field in event metadata; the utility does not infer pricing.

## Project status

```bash
python3 scripts/parliament_state.py project-status
```

The command scans `.project-files/roadmap/*/tasks.md` for task headings and
`Status: Complete` markers.
