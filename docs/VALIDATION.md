# Validation

Run from any directory (the script resolves its own repository by default, or
accepts `--root` for an isolated source copy):

```bash
python3 /path/to/Parliament-of-Codex/scripts/validate_repository.py
python3 -m unittest discover -s /path/to/Parliament-of-Codex/tests -v
git -C /path/to/Parliament-of-Codex diff --check
```

The dependency-free validator strictly parses the frontmatter and supported
TOML subset on Python 3.9+. It verifies 15 skills, 33 named agents, read-only
reviewers/orchestrator, manifest/version/prompts, qualified calls, 66 unique
structurally declared legacy action contracts, all-agent trust/stale-path rules,
canonical paths, internal Markdown links, and schema/template consumers. It
parses every JSON schema and checks the enforced contract keywords, but does not
claim full JSON Schema meta-validation without an external schema engine.

When `.project-files/` is present, it validates actual project-state lifecycle,
revision and canonical digest; actual council/review floor semantics; and actual
same-basename fast-track debt JSON/Markdown. With no artifact JSON, output says
so explicitly; adversarial contract fixtures exercise those branches in tests.

Optional upstream validators may require PyYAML; their missing optional
dependency is not a repository failure when the repository-owned validator and
tests pass. Run skill quick validation and plugin validation when their
dependencies are available, then inspect `git status --short`.
