# Migrate 0.2 Artifacts to 0.3

Version 0.3 changes the durable artifact topology. State records remain readable,
but durable artifacts require an explicit, reviewable migration. Stop council
writers before starting and do not delete the backups until the migrated tree is
approved.

## 1. Inventory and back up

From the target repository, record `find .project-files .parliament -maxdepth 4
-print` and `git status --short`. Redact secrets from the inventory. Create
recoverable siblings on the same filesystem:

```bash
cp -a .project-files .project-files.backup-0.2
cp -a .parliament .parliament.backup-0.2
```

If either backup already exists, stop and choose a new dated name. Never merge
into or overwrite an earlier backup.

## 2. Map durable files

Create targets only after checking that they do not exist:

| 0.2 source | 0.3 target |
| --- | --- |
| `.project-files/project-outline.md` | `.project-files/plan/project-outline.md` |
| `.project-files/feature-implementation.md` | `.project-files/plan/feature-implementation.md` |
| `.project-files/Roadmap.md` | `.project-files/plan/roadmap.md` |
| `.project-files/roadmap/<slug>/Spec.md` | `.project-files/work-items/<slug>/spec.md` |
| `.project-files/roadmap/<slug>/tasks.md` | `.project-files/work-items/<slug>/tasks.md` |
| `.project-files/adrs/<file>` | `.project-files/decisions/adrs/<file>` |
| standalone debate/decision records | `.project-files/decisions/debates/<file>` |
| existing council/review reports | `.project-files/reports/council/` or `.project-files/reports/reviews/` after classification |

Create `project-state.json` beside the plan and each work item. Begin migrated
content as `draft`, revision 1, with null approval. Re-review it, compute the
canonical directory digest from [the artifact contract](ARTIFACT_CONTRACT.md),
and only then record new approval.

Never overwrite a target collision. Compare both files; merge deliberately or
retain the 0.2 copy only in the backup. Keep unmapped/orphan files in the backup,
record their paths in the migration review, and classify them before deletion.
Do not silently move unknown files into a canonical directory.

## 3. Preserve or dispose of local state

`.parliament/snapshots/` and `.parliament/activity.jsonl` stay in place. The
0.3 utility safely reads legacy second-resolution snapshot IDs and normalizes
0.2 telemetry records in memory by adding `schema_version: 1` and `cost: null`;
it does not rewrite them during a query. A subsequent telemetry prune rewrites
retained records in the 0.3 shape. Legacy `.project-files/.telemetry/` is not a
supported state location: preserve it in the backup, manually classify any
needed JSON/JSONL, then dispose of it only after validation. Never migrate
secrets.

## 4. Validate

```bash
/usr/bin/python3 /path/to/Parliament-of-Codex/scripts/validate_repository.py --root /path/to/plugin-source
python3 /path/to/Parliament-of-Codex/scripts/parliament_state.py --root /path/to/target project-status
python3 /path/to/Parliament-of-Codex/scripts/parliament_state.py --root /path/to/target snapshot list
python3 /path/to/Parliament-of-Codex/scripts/parliament_state.py --root /path/to/target telemetry query --since 52w
```

Review collision/orphan decisions, compare file counts and Git diff, and obtain
fresh correctness/security review before deleting old artifact paths.

## 5. Roll back

Stop writers. Move the incomplete 0.3 `.project-files/` and `.parliament/`
aside without overwriting them, then restore the two 0.2 backup directories to
their original names. Re-run the 0.2 workflow in a fresh session. Rollback does
not reverse external actions or reports created elsewhere; record those
separately.
