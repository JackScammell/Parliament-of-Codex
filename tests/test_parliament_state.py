import json
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "parliament_state.py"


class ParliamentStateTests(unittest.TestCase):
    def call(self, root, *args, check=True, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), *args],
            text=True, capture_output=True, check=check, env=env,
        )

    def run_json(self, root, *args):
        return json.loads(self.call(root, *args).stdout)

    def create_snapshot(self, root):
        result = self.call(root, "snapshot", "create", "--label", "test", "--summary", "safe", check=False)
        self.assertEqual(
            result.returncode, 0,
            "snapshot subprocess failed\nstdout:\n%s\nstderr:\n%s" % (result.stdout, result.stderr),
        )
        return Path(result.stdout.strip())

    def test_normal_snapshot_telemetry_cost_metrics_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / ".project-files" / "work-items" / "demo" / "tasks.md"
            task_path.parent.mkdir(parents=True)
            task_path.write_text(
                "## Task 1: Done\n- Status: Complete\nnot status: complete\n"
                "## Task 2: Active\n- Status: In-progress\n"
                "## Task 3: Ready\n- Status: Scoped\n"
                "## Task 4: Later\n- Status: Unstarted\n", encoding="utf-8"
            )
            snapshot = self.create_snapshot(root)
            self.assertTrue(snapshot.exists())
            value = self.run_json(root, "snapshot", "show", snapshot.stem)
            self.assertEqual(value["label"], "test")
            event = self.run_json(
                root, "telemetry", "record", "--event", "CouncilCompleted",
                "--agent", "council-orchestrator", "--outcome", "APPROVE",
                "--duration-ms", "42", "--tokens", "10", "--cost-amount", "1.25",
                "--cost-currency", "GBP", "--cost-source", "user-supplied invoice",
            )
            self.assertEqual(event["schema_version"], 1)
            self.assertEqual(self.run_json(root, "telemetry", "query", "--group-by", "agent"), {"council-orchestrator": 1})
            metrics = self.run_json(root, "metrics", "--by", "agent")["council-orchestrator"]
            self.assertEqual(metrics["tokens"], 10)
            self.assertEqual(metrics["costs"], {"GBP": 1.25})
            status_value = self.run_json(root, "project-status")["items"][0]
            self.assertEqual(status_value["tasks"], 4)
            self.assertEqual([status_value[s] for s in ("complete", "in-progress", "scoped", "unstarted")], [1, 1, 1, 1])

    def test_rapid_and_concurrent_snapshots_are_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with ThreadPoolExecutor(max_workers=8) as pool:
                paths = list(pool.map(lambda _: self.create_snapshot(root), range(24)))
            self.assertEqual(len(set(paths)), 24)
            self.assertTrue(all(path.exists() for path in paths))

    def test_snapshot_traversal_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            bad = self.call(root, "snapshot", "show", "../secret", check=False)
            self.assertNotEqual(bad.returncode, 0)
            (root / ".parliament").symlink_to(outside, target_is_directory=True)
            rejected = self.call(root, "snapshot", "create", check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("symlink", rejected.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = self.create_snapshot(root)
            self.run_json(root, "telemetry", "record", "--event", "safe")
            self.assertEqual(stat.S_IMODE((root / ".parliament").stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE((root / ".parliament" / "activity.jsonl").stat().st_mode), 0o600)

    def test_metadata_and_nonnegative_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for args in [
                ("snapshot", "create", "--metadata", "[]"),
                ("telemetry", "record", "--event", "x", "--tokens", "-1"),
                ("telemetry", "record", "--event", "x", "--duration-ms", "-1"),
                ("telemetry", "record", "--event", "x", "--cost-amount", "1"),
                ("snapshot", "prune", "--keep", "-1"),
            ]:
                result = self.call(root, *args, check=False)
                self.assertNotEqual(result.returncode, 0, args)

    def test_non_git_root_uses_unknown_dirty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = self.create_snapshot(root)
            self.assertEqual(json.loads(snapshot.read_text())["git"], {"head": None, "branch": None, "dirty": None})

    def test_git_command_absence_uses_unknown_dirty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.call(root, "snapshot", "create", env={"PATH": ""})
            snapshot = Path(result.stdout.strip())
            self.assertEqual(json.loads(snapshot.read_text())["git"]["dirty"], None)

    def test_read_queries_do_not_create_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.run_json(root, "snapshot", "list"), [])
            self.assertEqual(self.run_json(root, "telemetry", "query"), [])
            self.assertEqual(self.run_json(root, "metrics"), {})
            self.assertFalse((root / ".parliament").exists())

    def test_malformed_telemetry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / ".parliament"
            state.mkdir()
            (state / "activity.jsonl").write_text('{"bad":true}\n', encoding="utf-8")
            result = self.call(root, "telemetry", "query", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("line 1", result.stderr)

    def test_retention_and_confirmed_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_json(root, "telemetry", "record", "--event", "new")
            path = root / ".parliament" / "activity.jsonl"
            old = {
                "schema_version": 1,
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                "event": "old", "agent": None, "outcome": None,
                "duration_ms": None, "tokens": None, "cost": None, "metadata": {},
            }
            path.write_text(json.dumps(old) + "\n" + path.read_text(), encoding="utf-8")
            result = self.run_json(root, "telemetry", "prune", "--older-than", "7d")
            self.assertEqual(result, {"retained": 1, "removed": 1})
            denied = self.call(root, "telemetry", "clear", "--confirm", "no", check=False)
            self.assertNotEqual(denied.returncode, 0)
            self.assertTrue(path.exists())
            self.assertEqual(self.run_json(root, "telemetry", "clear", "--confirm", "DELETE"), {"removed": True})

    def test_snapshot_prune_ignores_unowned_and_symlink_files(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            snapshots = [self.create_snapshot(root) for _ in range(3)]
            directory_path = root / ".parliament" / "snapshots"
            unrelated = directory_path / "notes.json"
            unrelated.write_text("{}", encoding="utf-8")
            link = directory_path / "20000101T000000.000000Z-000000000000.json"
            link.symlink_to(Path(outside) / "absent")
            result = self.run_json(root, "snapshot", "prune", "--keep", "1")
            self.assertEqual(len(result["removed"]), 2)
            self.assertTrue(unrelated.exists())
            self.assertTrue(link.is_symlink())

    def test_telemetry_symlink_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            state = root / ".parliament"
            state.mkdir()
            target = Path(outside) / "target.jsonl"
            target.write_text("sentinel\n", encoding="utf-8")
            (state / "activity.jsonl").symlink_to(target)
            result = self.call(root, "telemetry", "record", "--event", "x", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel\n")

    def test_hardlinked_writable_state_is_rejected_without_touching_outside_inode(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); state = root / ".parliament"; state.mkdir()
            target = Path(outside) / "activity.jsonl"
            existing = {
                "schema_version": 1, "timestamp": datetime.now(timezone.utc).isoformat(), "event": "existing",
                "agent": None, "outcome": None, "duration_ms": None, "tokens": None,
                "cost": None, "metadata": {},
            }
            original = json.dumps(existing) + "\n"; target.write_text(original, encoding="utf-8")
            target.chmod(0o640); original_mode = stat.S_IMODE(target.stat().st_mode)
            os.link(str(target), str(state / "activity.jsonl"))
            for args in [
                ("telemetry", "record", "--event", "x"),
                ("telemetry", "prune", "--older-than", "7d"),
                ("telemetry", "clear", "--confirm", "DELETE"),
            ]:
                with self.subTest(args=args):
                    result = self.call(root, *args, check=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("exactly one link", result.stderr)
                    self.assertEqual(target.read_text(encoding="utf-8"), original)
                    self.assertEqual(stat.S_IMODE(target.stat().st_mode), original_mode)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); state = root / ".parliament"; state.mkdir()
            target = Path(outside) / "lock"; target.write_text("sentinel", encoding="utf-8"); target.chmod(0o640)
            original_mode = stat.S_IMODE(target.stat().st_mode)
            os.link(str(target), str(state / ".lock"))
            result = self.call(root, "telemetry", "record", "--event", "x", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one link", result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "sentinel")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), original_mode)

    def test_lock_publication_loser_uses_shared_recovery_path(self):
        spec = importlib.util.spec_from_file_location("parliament_state_lock_test", SCRIPT)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory); state_fd = os.open(str(state), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            real_existing = module._open_existing_lock_at; real_link = os.link; calls = []
            def existing(directory_fd):
                calls.append(directory_fd)
                if len(calls) == 1: raise FileNotFoundError("first contender observed no lock")
                return real_existing(directory_fd)
            def publish_winner(*unused_args, **unused_kwargs):
                winner = state / ".lock.1111111111111111.tmp"; winner.write_text("", encoding="utf-8")
                real_link(str(winner), str(state / ".lock"))
                raise FileExistsError("winner published first")
            try:
                with mock.patch.object(module, "_open_existing_lock_at", side_effect=existing), mock.patch.object(module.os, "link", side_effect=publish_winner):
                    lock_fd = module._open_lock_at(state_fd)
                try: self.assertEqual(os.fstat(lock_fd).st_nlink, 1)
                finally: os.close(lock_fd)
                self.assertEqual(len(calls), 2)
                self.assertFalse(any(path.name.endswith(".tmp") for path in state.iterdir()))
            finally:
                os.close(state_fd)

    def test_legacy_0_2_snapshot_and_telemetry_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / ".parliament" / "snapshots"
            snapshots.mkdir(parents=True)
            legacy_id = "2026-01-02T03-04-05Z"
            legacy_snapshot = {
                "schema_version": 1, "snapshot_id": legacy_id, "label": "legacy",
                "created_at": "2026-01-02T03:04:05+00:00", "cwd": str(root),
                "git": {"head": None, "branch": None, "dirty": None},
                "summary": "0.2", "metadata": {},
            }
            (snapshots / (legacy_id + ".json")).write_text(json.dumps(legacy_snapshot), encoding="utf-8")
            self.assertEqual(self.run_json(root, "snapshot", "show", legacy_id)["label"], "legacy")
            legacy_event = {
                "timestamp": datetime.now(timezone.utc).isoformat(), "event": "legacy",
                "agent": None, "outcome": None, "duration_ms": 1, "tokens": 2, "metadata": {},
            }
            (root / ".parliament" / "activity.jsonl").write_text(json.dumps(legacy_event) + "\n", encoding="utf-8")
            normalized = self.run_json(root, "telemetry", "query", "--since", "52w")[0]
            self.assertEqual(normalized["schema_version"], 1)
            self.assertIsNone(normalized["cost"])

    def test_snapshot_subdirectory_symlink_and_corrupt_owned_snapshot_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / ".parliament").mkdir()
            (root / ".parliament" / "snapshots").symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.call(root, "snapshot", "list", check=False).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / ".parliament" / "snapshots"
            snapshots.mkdir(parents=True)
            (snapshots / "20260102T030405.000000Z-000000000000.json").write_text("{bad", encoding="utf-8")
            result = self.call(root, "snapshot", "list", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid snapshot", result.stderr)

    def test_summary_file_must_be_small_regular_and_confined(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "summary.txt"
            external.write_text("outside", encoding="utf-8")
            self.assertNotEqual(self.call(root, "snapshot", "create", "--summary-file", str(external), check=False).returncode, 0)
            large = root / "large.txt"
            large.write_text("x" * 5000, encoding="utf-8")
            self.assertNotEqual(self.call(root, "snapshot", "create", "--summary-file", "large.txt", check=False).returncode, 0)
            link_dir = root / "link"
            link_dir.symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.call(root, "snapshot", "create", "--summary-file", "link/summary.txt", check=False).returncode, 0)

    def test_task_status_failures_fences_and_symlink_ancestors(self):
        cases = {
            "missing": "## Task 1: X\n",
            "duplicate": "## Task 1: X\n- Status: scoped\n- Status: complete\n",
            "unknown": "## Task 1: X\n- Status: someday\n",
        }
        for name, content in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); path = root / ".project-files" / "work-items" / "x" / "tasks.md"
                path.parent.mkdir(parents=True); path.write_text(content, encoding="utf-8")
                self.assertNotEqual(self.call(root, "project-status", check=False).returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / ".project-files" / "work-items" / "x" / "tasks.md"
            path.parent.mkdir(parents=True)
            path.write_text("```md\n## Task 0\n- Status: nonsense\n```\n## Task 1\n- Status: complete\n", encoding="utf-8")
            self.assertEqual(self.run_json(root, "project-status")["items"][0]["tasks"], 1)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); (root / ".project-files").symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.call(root, "project-status", check=False).returncode, 0)

    def test_table_driven_telemetry_contract_rejections(self):
        base = {
            "schema_version": 1, "timestamp": "2026-01-02T03:04:05+00:00", "event": "x",
            "agent": None, "outcome": None, "duration_ms": None, "tokens": None,
            "cost": None, "metadata": {},
        }
        variants = []
        for key in base:
            item = dict(base); item.pop(key); variants.append(("missing-" + key, item))
        item = dict(base); item["extra"] = 1; variants.append(("extra", item))
        item = dict(base); item["tokens"] = "1"; variants.append(("type", item))
        item = dict(base); item["event"] = " "; variants.append(("blank", item))
        item = dict(base); item["cost"] = {"amount": 1, "currency": "gbp", "source": "x"}; variants.append(("currency", item))
        item = dict(base); item["cost"] = {"amount": float("inf"), "currency": "GBP", "source": "x"}; variants.append(("nonfinite", item))
        item = dict(base); item["metadata"] = {"x": "y" * 20000}; variants.append(("size", item))
        for name, value in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); state = root / ".parliament"; state.mkdir()
                (state / "activity.jsonl").write_text(json.dumps(value) + "\n", encoding="utf-8")
                self.assertNotEqual(self.call(root, "telemetry", "query", check=False).returncode, 0)

    def test_duration_limit_multicurrency_and_concurrent_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertNotEqual(self.call(root, "telemetry", "query", "--since=-1d", check=False).returncode, 0)
            self.assertNotEqual(self.call(root, "metrics", "--window=-1d", check=False).returncode, 0)
            self.assertNotEqual(self.call(root, "telemetry", "query", "--limit", "101", check=False).returncode, 0)
            for currency in ("GBP", "USD"):
                self.run_json(root, "telemetry", "record", "--event", "cost", "--cost-amount", "1", "--cost-currency", currency, "--cost-source", "fixture")
            self.assertEqual(self.run_json(root, "metrics")["unknown"]["costs"], {"GBP": 1.0, "USD": 1.0})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def write(number):
                return self.call(root, "telemetry", "record", "--event", "e%d" % number).returncode
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(list(pool.map(write, range(40))), [0] * 40)
            self.assertEqual(len(self.run_json(root, "telemetry", "query", "--since", "52w", "--limit", "100")), 40)

    def test_cost_overflow_and_huge_integer_fail_cleanly(self):
        def event(amount):
            return {
                "schema_version": 1, "timestamp": datetime.now(timezone.utc).isoformat(), "event": "cost",
                "agent": None, "outcome": None, "duration_ms": None, "tokens": None,
                "cost": {"amount": amount, "currency": "GBP", "source": "fixture"}, "metadata": {},
            }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); state = root / ".parliament"; state.mkdir()
            path = state / "activity.jsonl"
            path.write_text("\n".join(json.dumps(event(10 ** 308), separators=(",", ":")) for unused in range(2)) + "\n", encoding="utf-8")
            result = self.call(root, "metrics", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("aggregated cost is not finite", result.stderr)
            self.assertNotIn("Infinity", result.stdout)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); state = root / ".parliament"; state.mkdir()
            (state / "activity.jsonl").write_text(json.dumps(event(10 ** 400)) + "\n", encoding="utf-8")
            result = self.call(root, "telemetry", "query", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cost amount", result.stderr)

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_git_clean_dirty_and_detached_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            (root / "a.txt").write_text("a", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "a.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "init"], check=True, capture_output=True)
            clean = json.loads(self.create_snapshot(root).read_text())["git"]
            self.assertFalse(clean["dirty"])
            (root / "a.txt").write_text("dirty", encoding="utf-8")
            dirty = json.loads(self.create_snapshot(root).read_text())["git"]
            self.assertTrue(dirty["dirty"])
            subprocess.run(["git", "-C", str(root), "checkout", "--detach"], check=True, capture_output=True)
            detached = json.loads(self.create_snapshot(root).read_text())["git"]
            self.assertEqual(detached["branch"], "")

    def test_snapshot_creation_cap_and_excess_prune_recovery(self):
        def value(root, number):
            snapshot_id = "20260102T030405.%06dZ-%012x" % (number, number)
            return snapshot_id, {
                "schema_version": 1, "snapshot_id": snapshot_id, "label": "fixture",
                "created_at": "2026-01-02T03:04:05+00:00", "cwd": str(root),
                "git": {"head": None, "branch": None, "dirty": None}, "summary": "x", "metadata": {},
            }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); snapshots = root / ".parliament" / "snapshots"; snapshots.mkdir(parents=True)
            for number in range(200):
                snapshot_id, record = value(root, number); (snapshots / (snapshot_id + ".json")).write_text(json.dumps(record), encoding="utf-8")
            self.assertNotEqual(self.call(root, "snapshot", "create", check=False).returncode, 0)
            snapshot_id, record = value(root, 200); (snapshots / (snapshot_id + ".json")).write_text(json.dumps(record), encoding="utf-8")
            result = self.run_json(root, "snapshot", "prune", "--keep", "3")
            self.assertEqual(result["kept"], 3); self.assertEqual(len(result["removed"]), 198)
            self.assertEqual(len(self.run_json(root, "snapshot", "list")), 3)

    def test_snapshot_entry_scan_is_bounded_and_mutations_reuse_locked_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); snapshots = root / ".parliament" / "snapshots"; snapshots.mkdir(parents=True)
            for number in range(1001): (snapshots / ("note-%04d" % number)).write_text("x", encoding="utf-8")
            result = self.call(root, "snapshot", "list", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("too many entries", result.stderr)
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('with state_subdir_at(state_fd, "snapshots", base / "snapshots", create=True)', source)
        self.assertIn('with state_subdir_at(state_fd, "snapshots", base / "snapshots", create=False)', source)
        self.assertNotIn('with secure_state(root, "snapshots", create=True)', source)

    def test_telemetry_creation_cap_and_excess_prune_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); state = root / ".parliament"; state.mkdir()
            record = {
                "schema_version": 1, "timestamp": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                "event": "old", "agent": None, "outcome": None, "duration_ms": None,
                "tokens": None, "cost": None, "metadata": {},
            }
            path = state / "activity.jsonl"; line = json.dumps(record, separators=(",", ":")) + "\n"
            path.write_text(line * 10000, encoding="utf-8")
            self.assertNotEqual(self.call(root, "telemetry", "record", "--event", "blocked", check=False).returncode, 0)
            with path.open("a", encoding="utf-8") as handle: handle.write(line)
            result = self.run_json(root, "telemetry", "prune", "--older-than", "7d")
            self.assertEqual(result, {"retained": 0, "removed": 10001})
            self.assertEqual(self.run_json(root, "telemetry", "query"), [])

    def test_project_status_rejects_each_symlink_branch(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); project = root / ".project-files"; project.mkdir()
            (project / "work-items").symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.call(root, "project-status", check=False).returncode, 0)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); work = root / ".project-files" / "work-items"; work.mkdir(parents=True)
            (work / "item").symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.call(root, "project-status", check=False).returncode, 0)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); item = root / ".project-files" / "work-items" / "item"; item.mkdir(parents=True)
            target = Path(outside) / "tasks.md"; target.write_text("## Task 1\n- Status: complete\n", encoding="utf-8")
            (item / "tasks.md").symlink_to(target)
            self.assertNotEqual(self.call(root, "project-status", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
