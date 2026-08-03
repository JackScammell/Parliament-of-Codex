import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "scripts" / "validate_repository.py"


class RepositoryContractTests(unittest.TestCase):
    def copy_source(self, directory):
        target = Path(directory) / "source"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".parliament", ".project-files"))
        return target

    def run_validator(self, root, check=False):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(root)],
            text=True, capture_output=True, check=check,
        )

    def digest(self, directory):
        value = hashlib.sha256()
        for path in sorted(path for path in directory.iterdir() if path.name != "project-state.json" and path.is_file() and not path.is_symlink()):
            value.update(path.relative_to(directory).as_posix().encode("utf-8"))
            value.update(b"\0"); value.update(path.read_bytes()); value.update(b"\0")
        return value.hexdigest()

    def approved_state(self, directory, revision=1, digest=None):
        return {
            "schema_version": 1, "artifact": directory.name, "status": "approved", "revision": revision,
            "approval": {"approver": "owner", "approved_at": "2026-01-02T03:04:05+00:00", "revision": revision, "sha256": digest or self.digest(directory)},
        }

    def test_validator_runs_from_any_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(VALIDATOR)], cwd=directory,
                text=True, capture_output=True, check=True,
            )
        self.assertIn("66 structurally declared aliases", result.stdout)

    def test_all_json_contracts_parse(self):
        for path in sorted((ROOT / "schemas").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.3.0")

    def test_templates_have_lowercase_names(self):
        names = [path.name for path in (ROOT / "templates").iterdir() if path.is_file()]
        self.assertTrue(all(name == name.lower() for name in names))

    def test_validator_rejects_isolated_source_mutations(self):
        mutations = {
            "toml": lambda root: (root / ".codex" / "agents" / "api-specialist.toml").write_text((root / ".codex" / "agents" / "api-specialist.toml").read_text() + "\nbad = [\n", encoding="utf-8"),
            "frontmatter": lambda root: (root / "skills" / "council-core" / "SKILL.md").write_text((root / "skills" / "council-core" / "SKILL.md").read_text().replace("name: council-core", "name: council-core\nname: duplicate"), encoding="utf-8"),
            "action": lambda root: (root / "skills" / "council-plan" / "SKILL.md").write_text((root / "skills" / "council-plan" / "SKILL.md").read_text().replace("`roadmap-add-item`", "`removed-action`", 1), encoding="utf-8"),
            "stale": lambda root: (root / ".codex" / "agents" / "scope-weaver.toml").write_text((root / ".codex" / "agents" / "scope-weaver.toml").read_text().replace(".project-files/work-items/<slug>/", ".project-files/roadmap/"), encoding="utf-8"),
            "link": lambda root: (root / "README.md").write_text((root / "README.md").read_text() + "\n[broken](docs/does-not-exist.md)\n", encoding="utf-8"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); mutate(root)
                self.assertNotEqual(self.run_validator(root).returncode, 0)

    def test_project_state_actual_digest_and_lifecycle_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); plan = root / ".project-files" / "plan"; plan.mkdir(parents=True)
            (plan / "roadmap.md").write_text("approved bytes", encoding="utf-8")
            (plan / "project-state.json").write_text(json.dumps(self.approved_state(plan)), encoding="utf-8")
            self.assertEqual(self.run_validator(root).returncode, 0)
        variants = {
            "null-approval": lambda state, plan: state.update({"approval": None}),
            "revision-mismatch": lambda state, plan: state["approval"].update({"revision": 2}),
            "stale-digest": lambda state, plan: state["approval"].update({"sha256": "0" * 64}),
            "invalidated-missing": lambda state, plan: state.update({"status": "invalidated", "approval": None}),
        }
        for name, mutate in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); plan = root / ".project-files" / "plan"; plan.mkdir(parents=True)
                (plan / "roadmap.md").write_text("bytes", encoding="utf-8")
                state = self.approved_state(plan); mutate(state, plan)
                (plan / "project-state.json").write_text(json.dumps(state), encoding="utf-8")
                self.assertNotEqual(self.run_validator(root).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); plan = root / ".project-files" / "plan"; plan.mkdir(parents=True)
            state = {"schema_version": 1, "artifact": "plan", "status": "invalidated", "revision": 1, "approval": None, "invalidated_at": "2026-01-02T03:04:05+00:00", "invalidation_reason": "dependency changed"}
            (plan / "project-state.json").write_text(json.dumps(state), encoding="utf-8")
            self.assertEqual(self.run_validator(root).returncode, 0)

    def review(self):
        return {
            "schema_version": 1,
            "review_range": {"base": "HEAD^", "head": "HEAD", "included_paths": ["x"]},
            "reviewers": [
                {"role": "correctness-reviewer", "status": "reported", "verdict": "APPROVE", "evidence": "ok"},
                {"role": "security-reviewer", "status": "reported", "verdict": "APPROVE", "evidence": "ok"},
            ],
            "findings": [], "validation": [{"command": "test", "result": "pass", "evidence": "ok"}], "verdict": "APPROVE",
        }

    def finding(self):
        return {"id": "F1", "severity": "high", "blocking": True, "disposition": "open", "evidence": "line", "impact": "impact", "recommendation": "fix", "resolution": ""}

    def council(self, review_value):
        return {
            "schema_version": 1, "mode": "implement", "review_range": review_value["review_range"],
            "inventory": [{"path": "x", "summary": "x", "reuse_decision": "extend"}],
            "participants": ["implementation-owner"], "summary": "done", "validation": ["tests pass"],
            "reviewers": review_value["reviewers"],
            "unresolved_blocking_findings": sum(1 for item in review_value["findings"] if item["blocking"] is True and item["disposition"] == "open"),
            "review_report": ".project-files/reports/reviews/r.json", "decision": review_value["verdict"], "trade_offs": [],
        }

    def test_actual_review_council_and_debt_positive_and_adversarial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
            (reviews / "r.json").write_text(json.dumps(self.review()), encoding="utf-8")
            council = root / ".project-files" / "reports" / "council"; council.mkdir()
            report = self.council(self.review())
            (council / "c.json").write_text(json.dumps(report), encoding="utf-8")
            debt = root / ".project-files" / "review-debt"; debt.mkdir()
            debt_value = {"schema_version": 1, "id": "D1", "change": "x", "skipped_optional_reviews": ["testing-reviewer"], "owner": "owner", "due_at": "2026-02-02T03:04:05+00:00", "status": "open", "follow_up": "review"}
            (debt / "D1.json").write_text(json.dumps(debt_value), encoding="utf-8"); (debt / "D1.md").write_text("# D1", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stderr)
        adversarial = {
            "duplicate-floor": lambda value: value["reviewers"].append(dict(value["reviewers"][0])),
            "missing-floor": lambda value: value["reviewers"].pop(),
            "open-blocker": lambda value: value["findings"].append({"blocking": True, "disposition": "open"}),
            "contradictory": lambda value: value["reviewers"][0].update({"verdict": "CHANGES REQUESTED"}),
        }
        for name, mutate in adversarial.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
                value = self.review(); mutate(value); (reviews / "r.json").write_text(json.dumps(value), encoding="utf-8")
                self.assertNotEqual(self.run_validator(root).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); debt = root / ".project-files" / "review-debt"; debt.mkdir(parents=True)
            value = {"schema_version": 1, "id": "D1", "change": "x", "skipped_optional_reviews": ["testing-reviewer"], "owner": "owner", "due_at": "2026-02-02T03:04:05+00:00", "status": "open", "follow_up": "review"}
            (debt / "D1.json").write_text(json.dumps(value), encoding="utf-8")
            self.assertNotEqual(self.run_validator(root).returncode, 0)

    def test_nested_report_values_and_council_reconciliation_fail_closed(self):
        review_mutations = {
            "blocking-string": lambda value: value["findings"][0].update({"blocking": "true"}),
            "blocking-int": lambda value: value["findings"][0].update({"blocking": 1}),
            "severity": lambda value: value["findings"][0].update({"severity": "urgent"}),
            "disposition": lambda value: value["findings"][0].update({"disposition": "ignored"}),
            "empty-evidence": lambda value: value["reviewers"][0].update({"evidence": ""}),
        }
        for name, mutate in review_mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
                value = self.review(); value["verdict"] = "CHANGES REQUESTED"; value["reviewers"][0]["verdict"] = "CHANGES REQUESTED"; value["findings"] = [self.finding()]
                mutate(value); (reviews / "r.json").write_text(json.dumps(value), encoding="utf-8")
                self.assertNotEqual(self.run_validator(root).returncode, 0)
        council_mutations = {
            "bool-count": lambda value: value.update({"unresolved_blocking_findings": True}),
            "negative-count": lambda value: value.update({"unresolved_blocking_findings": -1}),
            "range-mismatch": lambda value: value["review_range"].update({"head": "OTHER"}),
            "decision-mismatch": lambda value: value.update({"decision": "CHANGES REQUESTED"}),
            "arbitrary-link": lambda value: value.update({"review_report": ".codex-plugin/plugin.json"}),
        }
        for name, linked in {
            "link-null": None, "link-bool": True, "link-number": 1,
            "link-object": {}, "link-array": [], "link-empty": "",
        }.items():
            council_mutations[name] = lambda value, linked=linked: value.update({"review_report": linked})
        for name, mutate in council_mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
                review = self.review(); (reviews / "r.json").write_text(json.dumps(review), encoding="utf-8")
                council_dir = root / ".project-files" / "reports" / "council"; council_dir.mkdir()
                value = self.council(review); mutate(value); (council_dir / "c.json").write_text(json.dumps(value), encoding="utf-8")
                self.assertNotEqual(self.run_validator(root).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
            target = reviews / "target.json"; target.write_text(json.dumps(self.review()), encoding="utf-8")
            (reviews / "r.json").symlink_to(target)
            council_dir = root / ".project-files" / "reports" / "council"; council_dir.mkdir()
            (council_dir / "c.json").write_text(json.dumps(self.council(self.review())), encoding="utf-8")
            self.assertNotEqual(self.run_validator(root).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); reviews = root / ".project-files" / "reports" / "reviews"; reviews.mkdir(parents=True)
            review = self.review(); review["verdict"] = "CHANGES REQUESTED"; review["reviewers"][0]["verdict"] = "CHANGES REQUESTED"; review["findings"] = [self.finding()]
            (reviews / "r.json").write_text(json.dumps(review), encoding="utf-8")
            council_dir = root / ".project-files" / "reports" / "council"; council_dir.mkdir()
            value = self.council(review); value["decision"] = "APPROVE"; value["unresolved_blocking_findings"] = 0
            value["reviewers"] = self.review()["reviewers"]
            (council_dir / "c.json").write_text(json.dumps(value), encoding="utf-8")
            self.assertNotEqual(self.run_validator(root).returncode, 0)

    def test_review_debt_accepts_only_optional_reviewer_roles(self):
        for role in ("correctness-reviewer", "security-reviewer", "unknown-reviewer"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); debt = root / ".project-files" / "review-debt"; debt.mkdir(parents=True)
                value = {"schema_version": 1, "id": "D1", "change": "x", "skipped_optional_reviews": [role], "owner": "owner", "due_at": "2026-02-02T03:04:05+00:00", "status": "open", "follow_up": "review"}
                (debt / "D1.json").write_text(json.dumps(value), encoding="utf-8")
                (debt / "D1.md").write_text("# D1", encoding="utf-8")
                result = self.run_validator(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("reviewer role", result.stderr)

    def test_populated_canonical_directories_require_state_and_digest_is_bounded(self):
        for relative in (("plan",), ("work-items", "item")):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = self.copy_source(directory); target = root / ".project-files"
                for part in relative: target = target / part
                target.mkdir(parents=True); (target / "artifact.md").write_text("content", encoding="utf-8")
                self.assertNotEqual(self.run_validator(root).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); plan = root / ".project-files" / "plan"; plan.mkdir(parents=True)
            (plan / "large.md").write_text("x" * 1_048_577, encoding="utf-8")
            state = self.approved_state(plan, digest="0" * 64); (plan / "project-state.json").write_text(json.dumps(state), encoding="utf-8")
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0); self.assertIn("too large", result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_source(directory); plan = root / ".project-files" / "plan"; plan.mkdir(parents=True)
            for number in range(101): (plan / ("%03d.md" % number)).write_text("x", encoding="utf-8")
            state = self.approved_state(plan, digest="0" * 64); (plan / "project-state.json").write_text(json.dumps(state), encoding="utf-8")
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0); self.assertIn("too many governed", result.stderr)


if __name__ == "__main__":
    unittest.main()
