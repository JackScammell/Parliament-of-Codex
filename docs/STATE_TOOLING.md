# State Tooling

`scripts/parliament_state.py` is dependency-free on Python 3.9+ and confines
writes to a real, nonsymlink `.parliament/` below `--root`. Mutations create
directories/files with POSIX modes 0700/0600 where supported and warn when the
directory is not ignored or is tracked. Read-only queries do not create state.
Secure operation requires POSIX descriptor-relative filesystem calls and
`O_NOFOLLOW`. The tool refuses to operate on Windows or any platform without
the required `dir_fd` and no-follow support; it does not fall back to
path-based mutation.

Run from the target repository and omit `--root`, or place the global `--root`
option before the subcommand:

```bash
python3 /path/to/parliament_state.py --root /path/to/target snapshot create --label before-migration --summary "Approved plan"
python3 /path/to/parliament_state.py --root /path/to/target snapshot list
python3 /path/to/parliament_state.py --root /path/to/target snapshot show <snapshot-id>
python3 /path/to/parliament_state.py --root /path/to/target snapshot prune --keep 20
```

Snapshot prune immediately and permanently deletes validated snapshot files
beyond the newest retained count; there is no restore command. Snapshots use
collision-resistant IDs and exclusive creation. Legacy 0.2 IDs remain readable. Git `head`,
`branch`, and `dirty` are `null` when Git/repository state is unavailable; null
must not be interpreted as clean. Metadata must be a bounded JSON object.

```bash
python3 /path/to/parliament_state.py --root /path/to/target telemetry record --event CouncilCompleted \
  --agent council-orchestrator --outcome APPROVE --duration-ms 42000 --tokens 1200 \
  --cost-amount 1.25 --cost-currency GBP --cost-source "user-supplied invoice"
python3 /path/to/parliament_state.py --root /path/to/target telemetry query --since 7d --group-by agent
python3 /path/to/parliament_state.py --root /path/to/target metrics --window 30d --by agent
python3 /path/to/parliament_state.py --root /path/to/target telemetry prune --older-than 90d
python3 /path/to/parliament_state.py --root /path/to/target telemetry clear --confirm DELETE
```

Telemetry is opt-in. Duration, token, limit, retention, and cost values are
nonnegative. Cost requires amount, three-letter currency, and source; metrics
never combine currencies or infer rates. Records are validated on read and
malformed lines fail closed. Telemetry prune immediately rewrites the file with
only retained records and permanently deletes older records; confirmed clear
immediately deletes the entire telemetry file. Neither operation has recovery
unless you made an external backup. Snapshots have separate destructive
retention via `snapshot prune`.

## Resource and recovery limits

- Normal snapshot creation and listing are capped at 200 snapshots. Snapshot
  directory scans are capped at 1,000 total entries; `snapshot prune` can
  recover more than 200 validated snapshots within that scan bound. Creation
  refuses at 200 and directs the operator to prune.
- Normal telemetry access is capped at 10,000 records and an 8 MiB file.
  Every telemetry line is capped at 64 KiB. `telemetry prune` and confirmed
  `telemetry clear` can recover an oversized telemetry file up to 64 MiB;
  prune still validates every record and enforces the 64 KiB line limit.
  Files beyond 64 MiB require external administrator recovery.
- Snapshot JSON and other ordinary state JSON reads are capped at 64 KiB.
  Metadata objects are capped at 16 KiB, and individual summary, event,
  identity, outcome, and cost-source strings are capped at 4 KiB.
- `project-status` reads at most 1,000 work items and caps each `tasks.md` at
  1 MiB. Exceeding either bound fails closed; there is no mutating recovery
  path because project status is read-only.

Prune and clear are the only built-in recovery paths above normal retention
limits. Snapshot prune works only within the 1,000-entry snapshot scan bound;
telemetry prune and clear work only within the 64 MiB recovery bound. Neither
operation bypasses symlink, hard-link, or regular-file validation, and prune
also validates every record. Clear deliberately removes the whole file without
parsing its records.

`project-status` parses `.project-files/work-items/*/tasks.md` and counts exact
`unstarted`, `scoped`, `in-progress`, and `complete` status fields. Every task
must have exactly one supported status; missing, duplicate, or unknown values
fail the command. Status-like text inside fenced code is ignored. The utility
never captures/restores private conversation state. Never put secrets or
personal data in summaries or metadata; deletion is the retention mechanism.
