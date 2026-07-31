#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path


def utc_now():
    return datetime.now(UTC)


def timestamp():
    return utc_now().strftime("%Y-%m-%dT%H-%M-%SZ")


def state_dir(root):
    path = Path(root).resolve() / ".parliament"
    path.mkdir(parents=True, exist_ok=True)
    return path


def git_value(root, *args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(Path(root).resolve()), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None


def read_json(path):
    with path.open() as handle:
        return json.load(handle)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
    temporary.replace(path)


def duration(value):
    if not value:
        return None
    unit = value[-1]
    if unit not in {"h", "d", "w"}:
        raise ValueError("duration must use h, d, or w")
    amount = int(value[:-1])
    return timedelta(hours=amount) if unit == "h" else timedelta(days=amount * {"d": 1, "w": 7}[unit])


def snapshot_create(args):
    root = Path(args.root).resolve()
    snapshots = state_dir(root) / "snapshots"
    snapshots.mkdir(exist_ok=True)
    summary = args.summary or ""
    if args.summary_file:
        summary = Path(args.summary_file).read_text()
    snapshot_id = timestamp()
    value = {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "label": args.label or "manual",
        "created_at": utc_now().isoformat(),
        "cwd": str(root),
        "git": {
            "head": git_value(root, "rev-parse", "HEAD"),
            "branch": git_value(root, "branch", "--show-current"),
            "dirty": bool(git_value(root, "status", "--porcelain")),
        },
        "summary": summary,
        "metadata": json.loads(args.metadata) if args.metadata else {},
    }
    path = snapshots / f"{snapshot_id}.json"
    write_json(path, value)
    print(path)


def snapshots(args):
    directory = state_dir(args.root) / "snapshots"
    directory.mkdir(exist_ok=True)
    paths = sorted(directory.glob("*.json"), reverse=True)
    if args.action == "list":
        print(json.dumps([read_json(path) for path in paths], indent=2))
        return
    if args.action == "show":
        path = directory / f"{args.snapshot_id}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        print(json.dumps(read_json(path), indent=2))
        return
    keep = max(args.keep, 3)
    removed = []
    for path in paths[keep:]:
        path.unlink()
        removed.append(path.name)
    print(json.dumps({"kept": min(len(paths), keep), "removed": removed}, indent=2))


def telemetry_path(root):
    return state_dir(root) / "activity.jsonl"


def record(args):
    record_value = {
        "timestamp": utc_now().isoformat(),
        "event": args.event,
        "agent": args.agent,
        "outcome": args.outcome,
        "duration_ms": args.duration_ms,
        "tokens": args.tokens,
        "metadata": json.loads(args.metadata) if args.metadata else {},
    }
    with telemetry_path(args.root).open("a") as handle:
        handle.write(json.dumps(record_value) + "\n")
    print(json.dumps(record_value, indent=2))


def telemetry_records(root, since):
    path = telemetry_path(root)
    if not path.exists():
        return []
    cutoff = utc_now() - duration(since) if since else None
    records = []
    for line in path.read_text().splitlines():
        value = json.loads(line)
        if cutoff and datetime.fromisoformat(value["timestamp"]) < cutoff:
            continue
        records.append(value)
    return records


def query(args):
    records = telemetry_records(args.root, args.since)
    records = [value for value in records if not args.event or value["event"] == args.event]
    records = [value for value in records if not args.agent or value.get("agent") == args.agent]
    if args.group_by:
        grouped = Counter(str(value.get(args.group_by, "unknown")) for value in records)
        print(json.dumps(dict(sorted(grouped.items())), indent=2))
        return
    print(json.dumps(records[:args.limit], indent=2))


def metrics(args):
    records = telemetry_records(args.root, args.window)
    groups = defaultdict(lambda: {"events": 0, "tokens": 0, "duration_ms": 0})
    for value in records:
        key = value.get(args.by, "unknown")
        groups[key]["events"] += 1
        groups[key]["tokens"] += value.get("tokens") or 0
        groups[key]["duration_ms"] += value.get("duration_ms") or 0
    print(json.dumps(dict(sorted(groups.items())), indent=2))


def project_status(args):
    root = Path(args.root).resolve() / ".project-files"
    roadmap = root / "roadmap"
    items = []
    if roadmap.exists():
        for directory in sorted(path for path in roadmap.iterdir() if path.is_dir()):
            task_file = directory / "tasks.md"
            text = task_file.read_text() if task_file.exists() else ""
            total = text.count("## Task")
            complete = text.lower().count("status: complete")
            items.append({"item": directory.name, "tasks": total, "complete": complete})
    print(json.dumps({"project_files": root.exists(), "items": items}, indent=2))


def parser():
    root = Path.cwd()
    result = argparse.ArgumentParser(description="Local Parliament of Codex state utility")
    result.add_argument("--root", default=root)
    commands = result.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot_commands = snapshot.add_subparsers(dest="action", required=True)
    create = snapshot_commands.add_parser("create")
    create.add_argument("--label")
    create.add_argument("--summary")
    create.add_argument("--summary-file")
    create.add_argument("--metadata")
    create.set_defaults(handler=snapshot_create)
    listing = snapshot_commands.add_parser("list")
    listing.set_defaults(handler=snapshots)
    show = snapshot_commands.add_parser("show")
    show.add_argument("snapshot_id")
    show.set_defaults(handler=snapshots)
    prune = snapshot_commands.add_parser("prune")
    prune.add_argument("--keep", type=int, default=20)
    prune.set_defaults(handler=snapshots)
    telemetry = commands.add_parser("telemetry")
    telemetry_commands = telemetry.add_subparsers(dest="action", required=True)
    telemetry_record = telemetry_commands.add_parser("record")
    telemetry_record.add_argument("--event", required=True)
    telemetry_record.add_argument("--agent")
    telemetry_record.add_argument("--outcome")
    telemetry_record.add_argument("--duration-ms", type=int)
    telemetry_record.add_argument("--tokens", type=int)
    telemetry_record.add_argument("--metadata")
    telemetry_record.set_defaults(handler=record)
    telemetry_query = telemetry_commands.add_parser("query")
    telemetry_query.add_argument("--event")
    telemetry_query.add_argument("--agent")
    telemetry_query.add_argument("--since", default="7d")
    telemetry_query.add_argument("--group-by")
    telemetry_query.add_argument("--limit", type=int, default=100)
    telemetry_query.set_defaults(handler=query)
    metric = commands.add_parser("metrics")
    metric.add_argument("--window", default="7d")
    metric.add_argument("--by", default="agent")
    metric.set_defaults(handler=metrics)
    status = commands.add_parser("project-status")
    status.set_defaults(handler=project_status)
    return result


def main():
    arguments = parser().parse_args()
    try:
        arguments.handler(arguments)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
