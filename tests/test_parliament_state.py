import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "parliament_state.py"


class ParliamentStateTests(unittest.TestCase):
    def run_state(self, root, *args):
        output = subprocess.check_output(
            ["python3", str(SCRIPT), "--root", str(root), *args], text=True
        )
        return json.loads(output)

    def test_snapshot_telemetry_metrics_and_project_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / ".project-files" / "roadmap" / "demo" / "tasks.md"
            task_path.parent.mkdir(parents=True)
            task_path.write_text("## Task 1: Demo\n- Status: Complete\n")

            snapshot_path = subprocess.check_output(
                [
                    "python3",
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "snapshot",
                    "create",
                    "--label",
                    "test",
                    "--summary",
                    "summary",
                ],
                text=True,
            ).strip()
            self.assertTrue(Path(snapshot_path).exists())
            snapshots = self.run_state(root, "snapshot", "list")
            self.assertEqual(snapshots[0]["label"], "test")

            self.run_state(
                root,
                "telemetry",
                "record",
                "--event",
                "CouncilCompleted",
                "--agent",
                "council-orchestrator",
                "--outcome",
                "APPROVE",
                "--duration-ms",
                "42",
                "--tokens",
                "10",
            )
            groups = self.run_state(root, "telemetry", "query", "--group-by", "agent")
            self.assertEqual(groups, {"council-orchestrator": 1})
            metrics = self.run_state(root, "metrics", "--by", "agent")
            self.assertEqual(metrics["council-orchestrator"]["tokens"], 10)

            status = self.run_state(root, "project-status")
            self.assertEqual(status["items"][0]["complete"], 1)


if __name__ == "__main__":
    unittest.main()
