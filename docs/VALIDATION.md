# Validation

## Structural checks

Run these checks from the repository root:

```bash
node -e 'JSON.parse(require("fs").readFileSync(".codex-plugin/plugin.json", "utf8"))'
git diff --check
```

The plugin creator's full validator additionally requires `PyYAML` in the
active Python environment:

```bash
python3 /Users/jack/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

## Workflow smoke tests

Use a disposable sample repository to confirm each workflow:

1. `$council-plan` produces the three project artifacts without product edits.
2. `$council-scope` creates a specification and task list for one item.
3. `$council-implement` collects correctness and security reports before a
   completion claim.
4. `$council-review` returns `APPROVE`, `CHANGES REQUESTED`, or `INCOMPLETE`.

Record unexpected behavior in the porting plan before adding more workflows.
