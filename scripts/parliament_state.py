#!/usr/bin/env python3
"""Dependency-free, repository-local state tooling for Parliament of Codex."""
import argparse
import contextlib
import heapq
import json
import math
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None
    import msvcrt

STATE_NAME = ".parliament"
SNAPSHOT_ID = re.compile(r"^\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{12}$")
LEGACY_SNAPSHOT_ID = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$")
TASK_HEADING = re.compile(r"^## Task(?:\s+\d+)?(?::|\s|$)", re.IGNORECASE)
STATUS_LINE = re.compile(r"^\s*(?:[-*]\s*)?Status:\s*(.+?)\s*$", re.IGNORECASE)
STATUSES = {"unstarted", "scoped", "in-progress", "complete"}
MAX_METADATA_BYTES = 16_384
MAX_STRING_BYTES = 4_096
MAX_STATE_FILE_BYTES = 65_536
MAX_TELEMETRY_FILE_BYTES = 8_388_608
MAX_TELEMETRY_RECOVERY_BYTES = 67_108_864
MAX_TELEMETRY_LINE_BYTES = 65_536
MAX_RECORDS = 10_000
MAX_SNAPSHOTS = 200
MAX_SNAPSHOT_ENTRIES = 1_000
MAX_TASK_FILE_BYTES = 1_048_576
MAX_WORK_ITEMS = 1_000
MAX_COST_AMOUNT = 1e308
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DIRECTORY = getattr(os, "O_DIRECTORY", 0)
REQUIRED_DIRFD = (os.open, os.mkdir, os.unlink, os.rename, os.link, os.stat)
GIT_PATH = shutil.which("git")


def utc_now():
    return datetime.now(timezone.utc)


def timestamp_id():
    return utc_now().strftime("%Y%m%dT%H%M%S.%fZ") + "-" + secrets.token_hex(6)


def _resolved_root(root):
    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        raise ValueError("root must be an existing directory")
    return path


def _within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _open_regular(path, flags, mode=0o600, max_bytes=None):
    fd = os.open(str(path), flags | NOFOLLOW, mode)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("state file must be a regular file")
        if max_bytes is not None and info.st_size > max_bytes:
            raise ValueError("state file is too large")
        if flags & (os.O_WRONLY | os.O_RDWR):
            os.fchmod(fd, 0o600)
        return fd
    except Exception:
        os.close(fd)
        raise


def _require_secure_dirfd():
    if not NOFOLLOW or any(function not in os.supports_dir_fd for function in REQUIRED_DIRFD):
        raise ValueError("secure descriptor-relative state I/O is unsupported on this platform")


@contextlib.contextmanager
def secure_state(root, subdir=None, create=False):
    _require_secure_dirfd()
    root_path = _resolved_root(root)
    root_fd = os.open(str(root_path), os.O_RDONLY | DIRECTORY | NOFOLLOW)
    state_fd = None; sub_fd = None
    try:
        try:
            state_fd = os.open(STATE_NAME, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=root_fd)
        except FileNotFoundError:
            if not create:
                yield root_path / STATE_NAME, None, None
                return
            try: os.mkdir(STATE_NAME, 0o700, dir_fd=root_fd)
            except FileExistsError: pass
            state_fd = os.open(STATE_NAME, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=root_fd)
            os.fchmod(state_fd, 0o700)
        if subdir:
            try:
                sub_fd = os.open(subdir, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=state_fd)
            except FileNotFoundError:
                if not create:
                    yield root_path / STATE_NAME / subdir, state_fd, None
                    return
                try: os.mkdir(subdir, 0o700, dir_fd=state_fd)
                except FileExistsError: pass
                sub_fd = os.open(subdir, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=state_fd)
                os.fchmod(sub_fd, 0o700)
        if create: warn_ignore_state(root_path)
        yield root_path / STATE_NAME / subdir if subdir else root_path / STATE_NAME, state_fd, sub_fd
    except OSError as error:
        if error.errno in {getattr(os, "ELOOP", 62), 20}:
            raise ValueError("state path must not contain symlinks")
        raise
    finally:
        if sub_fd is not None: os.close(sub_fd)
        if state_fd is not None: os.close(state_fd)
        os.close(root_fd)


@contextlib.contextmanager
def state_subdir_at(state_fd, name, path, create=False):
    sub_fd = None
    try:
        try:
            sub_fd = os.open(name, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=state_fd)
        except FileNotFoundError:
            if not create:
                yield path, None
                return
            try: os.mkdir(name, 0o700, dir_fd=state_fd)
            except FileExistsError: pass
            sub_fd = os.open(name, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=state_fd)
            os.fchmod(sub_fd, 0o700)
        yield path, sub_fd
    except OSError as error:
        if error.errno in {getattr(os, "ELOOP", 62), 20}:
            raise ValueError("state path must not contain symlinks")
        raise
    finally:
        if sub_fd is not None: os.close(sub_fd)


def _open_at(directory_fd, name, flags, mode=0o600, max_bytes=None, require_single_link=False, allow_linked=False):
    fd = os.open(name, flags | NOFOLLOW, mode, dir_fd=directory_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode): raise ValueError("state file must be a regular file")
        if max_bytes is not None and info.st_size > max_bytes: raise ValueError("state file is too large")
        writable = bool(flags & (os.O_WRONLY | os.O_RDWR))
        if (writable or require_single_link) and not allow_linked and info.st_nlink != 1: raise ValueError("writable state file must have exactly one link")
        if writable and not allow_linked: os.fchmod(fd, 0o600)
        return fd
    except Exception:
        os.close(fd); raise


def read_json_at(directory_fd, name):
    fd = _open_at(directory_fd, name, os.O_RDONLY, max_bytes=MAX_STATE_FILE_BYTES)
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=lambda item: (_ for _ in ()).throw(ValueError("non-finite JSON value: " + item)))


def atomic_json_at(directory_fd, name, value, exclusive=False):
    temporary = ".%s.%s.tmp" % (name, secrets.token_hex(8))
    fd = _open_at(directory_fd, temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        if exclusive:
            os.link(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
            os.unlink(temporary, dir_fd=directory_fd)
        else:
            os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
    finally:
        try: os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError: pass


def _open_existing_lock_at(directory_fd):
    fd = _open_at(directory_fd, ".lock", os.O_RDWR, max_bytes=1024, allow_linked=True)
    try:
        info = os.fstat(fd)
        if info.st_nlink == 2:
            with os.scandir(directory_fd) as entries:
                for number, entry in enumerate(entries, 1):
                    if number > 100: break
                    if not re.fullmatch(r"\.lock\.[0-9a-f]{16}\.tmp", entry.name): continue
                    try: candidate = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
                    except FileNotFoundError: continue
                    if (candidate.st_dev, candidate.st_ino) == (info.st_dev, info.st_ino):
                        try: os.unlink(entry.name, dir_fd=directory_fd)
                        except FileNotFoundError: pass
                        break
        if os.fstat(fd).st_nlink != 1:
            raise ValueError("writable state file must have exactly one link")
        os.fchmod(fd, 0o600)
        return fd
    except Exception:
        os.close(fd)
        raise


def _open_lock_at(directory_fd):
    try:
        return _open_existing_lock_at(directory_fd)
    except FileNotFoundError:
        pass
    temporary = ".lock.%s.tmp" % secrets.token_hex(8)
    fd = _open_at(directory_fd, temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600, 1024)
    try:
        try:
            os.link(temporary, ".lock", src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
        except FileExistsError:
            os.close(fd); fd = None
            return _open_existing_lock_at(directory_fd)
        try: os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError: pass
        result = fd; fd = None
        return result
    finally:
        if fd is not None: os.close(fd)
        try: os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError: pass


@contextlib.contextmanager
def state_lock(root):
    with secure_state(root, create=True) as (base, state_fd, unused):
        fd = _open_lock_at(state_fd)
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
            else:  # pragma: no cover - Windows refuses secure dirfd before this point
                raise ValueError("secure state locking is unsupported on this platform")
            yield base, state_fd
        finally:
            if fcntl is not None: fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def git_value(root, *args):
    if GIT_PATH is None:
        return None
    try:
        return subprocess.check_output(
            [GIT_PATH, "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "-C", str(_resolved_root(root)), *args],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def git_metadata(root):
    head = git_value(root, "rev-parse", "--verify", "HEAD")
    inside = git_value(root, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return {"head": None, "branch": None, "dirty": None}
    status = git_value(root, "status", "--porcelain")
    return {
        "head": head,
        "branch": git_value(root, "branch", "--show-current"),
        "dirty": None if status is None else bool(status),
    }


def warn_ignore_state(root):
    if GIT_PATH is None or git_value(root, "rev-parse", "--is-inside-work-tree") != "true":
        return
    ignored = subprocess.run(
        [GIT_PATH, "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "-C", str(root), "check-ignore", "-q", STATE_NAME + "/"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    tracked = bool(git_value(root, "ls-files", STATE_NAME))
    if not ignored or tracked:
        print("warning: .parliament/ must be ignored and untracked", file=sys.stderr)


def parse_object(raw, field="metadata"):
    if raw is None:
        return {}
    if len(raw.encode("utf-8")) > MAX_METADATA_BYTES:
        raise ValueError("%s is too large" % field)
    value = json.loads(raw, parse_constant=lambda item: (_ for _ in ()).throw(ValueError("non-finite JSON value: " + item)))
    if not isinstance(value, dict):
        raise ValueError("%s must be a JSON object" % field)
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_METADATA_BYTES:
        raise ValueError("%s is too large" % field)
    return value


def parse_duration(value):
    if value is None:
        return None
    match = re.fullmatch(r"(\d+)([hdw])", value)
    if not match:
        raise ValueError("duration must be a nonnegative integer followed by h, d, or w")
    amount = int(match.group(1))
    hours = amount * {"h": 1, "d": 24, "w": 168}[match.group(2)]
    if hours > 87_600:
        raise ValueError("duration must not exceed ten years")
    return timedelta(hours=hours)


def nonnegative(value, name):
    if value is not None and value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("telemetry timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid telemetry timestamp")
    if parsed.tzinfo is None:
        raise ValueError("telemetry timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def bounded_string(value, name, nullable=False):
    if nullable and value is None:
        return value
    if not isinstance(value, str) or (name in {"event", "cost source"} and not value.strip()):
        raise ValueError("%s must be %sa string" % (name, "null or " if nullable else ""))
    if len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise ValueError("%s is too large" % name)
    return value


def validate_snapshot(value, expected_id=None):
    if not isinstance(value, dict):
        raise ValueError("snapshot must be an object")
    required = {"schema_version", "snapshot_id", "label", "created_at", "cwd", "git", "summary", "metadata"}
    if set(value) != required or value.get("schema_version") != 1:
        raise ValueError("invalid snapshot record")
    if not (SNAPSHOT_ID.fullmatch(str(value.get("snapshot_id", ""))) or LEGACY_SNAPSHOT_ID.fullmatch(str(value.get("snapshot_id", "")))):
        raise ValueError("invalid snapshot id")
    if expected_id is not None and value["snapshot_id"] != expected_id:
        raise ValueError("snapshot id does not match filename")
    parse_timestamp(value["created_at"])
    for name in ("label", "cwd", "summary"):
        bounded_string(value[name], "snapshot " + name)
    git = value["git"]
    if not isinstance(git, dict) or set(git) != {"head", "branch", "dirty"}:
        raise ValueError("invalid snapshot Git metadata")
    if git["dirty"] is not None and not isinstance(git["dirty"], bool):
        raise ValueError("invalid snapshot dirty state")
    for name in ("head", "branch"):
        bounded_string(git[name], "Git " + name, nullable=True)
    encoded = json.dumps(value["metadata"], separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if not isinstance(value["metadata"], dict) or len(encoded) > MAX_METADATA_BYTES:
        raise ValueError("invalid snapshot metadata")
    return value


def validate_telemetry(value):
    if not isinstance(value, dict):
        raise ValueError("telemetry record must be an object")
    allowed = {"schema_version", "timestamp", "event", "agent", "outcome", "duration_ms", "tokens", "cost", "metadata"}
    if set(value) != allowed:
        raise ValueError("telemetry record must contain exactly the required fields")
    if value.get("schema_version") != 1:
        raise ValueError("unsupported telemetry schema_version")
    parse_timestamp(value.get("timestamp"))
    bounded_string(value.get("event"), "event")
    for name in ("agent", "outcome"):
        bounded_string(value.get(name), name, nullable=True)
    for name in ("duration_ms", "tokens"):
        item = value.get(name)
        if item is not None and (not isinstance(item, int) or isinstance(item, bool) or item < 0):
            raise ValueError("%s must be a nonnegative integer or null" % name)
    if not isinstance(value.get("metadata"), dict) or len(json.dumps(value["metadata"], separators=(",", ":"), ensure_ascii=False).encode("utf-8")) > MAX_METADATA_BYTES:
        raise ValueError("metadata must be an object")
    cost = value.get("cost")
    if cost is not None:
        if not isinstance(cost, dict) or set(cost) != {"amount", "currency", "source"}:
            raise ValueError("cost requires amount, currency, and source")
        amount = cost["amount"]
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0 or amount > MAX_COST_AMOUNT or (isinstance(amount, float) and not math.isfinite(amount)):
            raise ValueError("cost amount must be finite, nonnegative, and at most 1e308")
        if not isinstance(cost["currency"], str) or not re.fullmatch(r"[A-Z]{3}", cost["currency"]):
            raise ValueError("cost currency must be a three-letter uppercase code")
        bounded_string(cost["source"], "cost source")
    return value


def snapshot_create(args):
    root = _resolved_root(args.root)
    summary = args.summary or ""
    if args.summary_file:
        source = Path(args.summary_file)
        if not source.is_absolute():
            source = root / source
        lexical = Path(os.path.abspath(str(source)))
        if not _within(lexical, root):
            raise ValueError("summary file must be under root")
        cursor = root
        for part in lexical.relative_to(root).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ValueError("summary file path must not contain symlinks")
        resolved = source.resolve(strict=True)
        if not _within(resolved, root) or not resolved.is_file():
            raise ValueError("summary file must be a regular file under root")
        fd = _open_regular(resolved, os.O_RDONLY, max_bytes=MAX_STRING_BYTES)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            summary = handle.read(MAX_STRING_BYTES + 1)
    if len(summary.encode("utf-8")) > MAX_STRING_BYTES:
        raise ValueError("summary is too large")
    git = git_metadata(root)
    with state_lock(root) as (base, state_fd):
        with state_subdir_at(state_fd, "snapshots", base / "snapshots", create=True) as (directory, snapshot_fd):
            for count, unused in enumerate(iter_snapshots(snapshot_fd), 1):
                if count >= MAX_SNAPSHOTS: raise ValueError("snapshot creation cap reached; prune snapshots first")
            for _ in range(10):
                snapshot_id = timestamp_id()
                value = {
                    "schema_version": 1, "snapshot_id": snapshot_id,
                    "label": args.label or "manual", "created_at": utc_now().isoformat(),
                    "cwd": str(root), "git": git, "summary": summary,
                    "metadata": parse_object(args.metadata),
                }
                validate_snapshot(value, snapshot_id)
                name = snapshot_id + ".json"
                try:
                    atomic_json_at(snapshot_fd, name, value, exclusive=True)
                    print(directory / name)
                    return
                except FileExistsError:
                    continue
    raise ValueError("could not allocate a unique snapshot id")


def iter_snapshots(directory_fd):
    with os.scandir(directory_fd) as entries:
        for number, entry in enumerate(entries, 1):
            if number > MAX_SNAPSHOT_ENTRIES: raise ValueError("snapshot directory contains too many entries to process safely")
            name = entry.name
            if not name.endswith(".json"): continue
            snapshot_id = name[:-5]
            if not (SNAPSHOT_ID.fullmatch(snapshot_id) or LEGACY_SNAPSHOT_ID.fullmatch(snapshot_id)): continue
            if entry.is_symlink() or not entry.is_file(follow_symlinks=False): continue
            try: value = validate_snapshot(read_json_at(directory_fd, name), snapshot_id)
            except (ValueError, json.JSONDecodeError, OSError) as error: raise ValueError("invalid snapshot %s: %s" % (name, error))
            yield name, value


def _snapshots_at(args, directory, snapshot_fd):
        if snapshot_fd is None:
            if args.action == "show": raise FileNotFoundError("snapshot not found")
            print("[]" if args.action == "list" else json.dumps({"kept": 0, "removed": []}, indent=2)); return
        if args.action == "list":
            values = []
            for item in iter_snapshots(snapshot_fd):
                values.append(item)
                if len(values) > MAX_SNAPSHOTS: raise ValueError("too many snapshots to list; prune first")
            print(json.dumps([value for name, value in sorted(values, reverse=True)], indent=2)); return
        if args.action == "show":
            if not (SNAPSHOT_ID.fullmatch(args.snapshot_id) or LEGACY_SNAPSHOT_ID.fullmatch(args.snapshot_id)): raise ValueError("invalid snapshot id")
            try: value = validate_snapshot(read_json_at(snapshot_fd, args.snapshot_id + ".json"), args.snapshot_id)
            except FileNotFoundError: raise FileNotFoundError("snapshot not found")
            print(json.dumps(value, indent=2)); return
        keep = nonnegative(args.keep, "keep")
        total = sum(1 for unused in iter_snapshots(snapshot_fd))
        retained = []; removed = []
        for name, unused in iter_snapshots(snapshot_fd):
            heapq.heappush(retained, name)
            if len(retained) > keep:
                candidate = heapq.heappop(retained)
                os.unlink(candidate, dir_fd=snapshot_fd); removed.append(candidate)
        print(json.dumps({"kept": min(total, keep), "removed": sorted(removed)}, indent=2))


def snapshots(args):
    if args.action == "prune":
        with state_lock(args.root) as (base, state_fd):
            with state_subdir_at(state_fd, "snapshots", base / "snapshots", create=False) as (directory, snapshot_fd):
                return _snapshots_at(args, directory, snapshot_fd)
    with secure_state(args.root, "snapshots", create=False) as (directory, state_fd, snapshot_fd):
        return _snapshots_at(args, directory, snapshot_fd)


def normalize_telemetry_line(line, number):
    if len(line.encode("utf-8")) > MAX_TELEMETRY_LINE_BYTES: raise ValueError("telemetry record on line %d is too large" % number)
    try:
        value = json.loads(line, parse_constant=lambda item: (_ for _ in ()).throw(ValueError("non-finite JSON value: " + item)))
        legacy = {"timestamp", "event", "agent", "outcome", "duration_ms", "tokens", "metadata"}
        if isinstance(value, dict) and set(value) == legacy:
            value = dict(value); value["schema_version"] = 1; value["cost"] = None
        return validate_telemetry(value)
    except (ValueError, json.JSONDecodeError) as error:
        raise ValueError("invalid telemetry record on line %d: %s" % (number, error))


def telemetry_records_at(state_fd, since=None, enforce_cap=True, max_bytes=MAX_TELEMETRY_FILE_BYTES):
    cutoff = utc_now() - parse_duration(since) if since else None
    try: fd = _open_at(state_fd, "activity.jsonl", os.O_RDONLY, max_bytes=max_bytes)
    except FileNotFoundError: return []
    records = []
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if enforce_cap and number > MAX_RECORDS: raise ValueError("too many telemetry records; prune telemetry first")
            if not line.strip(): continue
            value = normalize_telemetry_line(line, number)
            if not cutoff or parse_timestamp(value["timestamp"]) >= cutoff: records.append(value)
    return records


def record(args):
    cost_fields = (args.cost_amount, args.cost_currency, args.cost_source)
    if any(item is not None for item in cost_fields) and not all(item is not None for item in cost_fields):
        raise ValueError("cost requires --cost-amount, --cost-currency, and --cost-source")
    value = {
        "schema_version": 1, "timestamp": utc_now().isoformat(), "event": args.event,
        "agent": args.agent, "outcome": args.outcome,
        "duration_ms": nonnegative(args.duration_ms, "duration-ms"),
        "tokens": nonnegative(args.tokens, "tokens"),
        "cost": None if not all(item is not None for item in cost_fields) else {
            "amount": nonnegative(args.cost_amount, "cost-amount"),
            "currency": args.cost_currency, "source": args.cost_source,
        },
        "metadata": parse_object(args.metadata),
    }
    validate_telemetry(value)
    encoded = (json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_TELEMETRY_LINE_BYTES:
        raise ValueError("telemetry record is too large")
    with state_lock(args.root) as (base, state_fd):
        if len(telemetry_records_at(state_fd)) >= MAX_RECORDS: raise ValueError("telemetry creation cap reached; prune telemetry first")
        fd = _open_at(state_fd, "activity.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600, MAX_TELEMETRY_FILE_BYTES)
        try:
            if os.fstat(fd).st_size + len(encoded) > MAX_TELEMETRY_FILE_BYTES:
                raise ValueError("telemetry file is too large")
            os.write(fd, encoded)
            os.fsync(fd)
        finally:
            os.close(fd)
    print(json.dumps(value, indent=2))


def telemetry_records(root, since=None):
    cutoff = utc_now() - parse_duration(since) if since else None
    with secure_state(root, create=False) as (base, state_fd, unused):
        if state_fd is None: return []
        return telemetry_records_at(state_fd, since)


def query(args):
    nonnegative(args.limit, "limit")
    if args.limit > 100:
        raise ValueError("limit must not exceed 100")
    records = telemetry_records(args.root, args.since)
    records = [v for v in records if not args.event or v["event"] == args.event]
    records = [v for v in records if not args.agent or v.get("agent") == args.agent]
    if args.group_by:
        grouped = Counter(str(v.get(args.group_by, "unknown")) for v in records)
        print(json.dumps(dict(sorted(grouped.items())), indent=2)); return
    print(json.dumps(records[:args.limit], indent=2))


def metrics(args):
    records = telemetry_records(args.root, args.window)
    groups = defaultdict(lambda: {"events": 0, "tokens": 0, "duration_ms": 0, "costs": {}})
    for value in records:
        key = str(value.get(args.by) or "unknown")
        groups[key]["events"] += 1
        groups[key]["tokens"] += value.get("tokens") or 0
        groups[key]["duration_ms"] += value.get("duration_ms") or 0
        if value.get("cost"):
            currency = value["cost"]["currency"]
            total = groups[key]["costs"].get(currency, 0) + value["cost"]["amount"]
            if total > MAX_COST_AMOUNT or (isinstance(total, float) and not math.isfinite(total)):
                raise ValueError("aggregated cost is not finite")
            groups[key]["costs"][currency] = total
    print(json.dumps(dict(sorted(groups.items())), indent=2, allow_nan=False))


def telemetry_prune(args):
    cutoff = utc_now() - parse_duration(args.older_than)
    retained = 0; removed = 0
    with state_lock(args.root) as (base, state_fd):
        try: source_fd = _open_at(state_fd, "activity.jsonl", os.O_RDONLY, max_bytes=MAX_TELEMETRY_RECOVERY_BYTES, require_single_link=True)
        except FileNotFoundError:
            print(json.dumps({"retained": 0, "removed": 0}, indent=2)); return
        temporary = ".activity.%s.tmp" % secrets.token_hex(8)
        target_fd = _open_at(state_fd, temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(source_fd, "r", encoding="utf-8") as source:
                for number, line in enumerate(source, 1):
                    if not line.strip(): continue
                    value = normalize_telemetry_line(line, number)
                    if parse_timestamp(value["timestamp"]) >= cutoff:
                        encoded = (json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8")
                        os.write(target_fd, encoded); retained += 1
                    else: removed += 1
            os.fsync(target_fd); os.close(target_fd); target_fd = None
            os.replace(temporary, "activity.jsonl", src_dir_fd=state_fd, dst_dir_fd=state_fd)
        finally:
            if target_fd is not None: os.close(target_fd)
            try: os.unlink(temporary, dir_fd=state_fd)
            except FileNotFoundError: pass
    print(json.dumps({"retained": retained, "removed": removed}, indent=2))


def telemetry_clear(args):
    if args.confirm != "DELETE":
        raise ValueError("telemetry clear requires --confirm DELETE")
    with state_lock(args.root) as (base, state_fd):
        removed = False
        try:
            fd = _open_at(state_fd, "activity.jsonl", os.O_RDONLY, max_bytes=MAX_TELEMETRY_RECOVERY_BYTES, require_single_link=True); os.close(fd)
            os.unlink("activity.jsonl", dir_fd=state_fd); removed = True
        except FileNotFoundError: pass
    print(json.dumps({"removed": removed}, indent=2))


def parse_tasks(text):
    tasks = []
    current = None
    fenced = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if TASK_HEADING.match(line):
            if current is not None:
                tasks.append(current)
            current = {"title": line.lstrip("# ").strip(), "status": None}
            continue
        match = STATUS_LINE.match(line)
        if current is not None and match:
            status = match.group(1).strip().lower().replace(" ", "-")
            if status not in STATUSES:
                raise ValueError("unsupported task status: %s" % match.group(1).strip())
            if current["status"] is not None:
                raise ValueError("duplicate task status: %s" % current["title"])
            current["status"] = status
    if current is not None:
        tasks.append(current)
    missing = [task["title"] for task in tasks if task["status"] is None]
    if missing:
        raise ValueError("missing task status: %s" % missing[0])
    return tasks


def project_status(args):
    _require_secure_dirfd()
    repository = _resolved_root(args.root)
    root_fd = os.open(str(repository), os.O_RDONLY | DIRECTORY | NOFOLLOW)
    items = []
    project_fd = None; work_fd = None
    try:
        try: project_fd = os.open(".project-files", os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=root_fd)
        except FileNotFoundError:
            print(json.dumps({"project_files": False, "items": []}, indent=2)); return
        try: work_fd = os.open("work-items", os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=project_fd)
        except FileNotFoundError:
            print(json.dumps({"project_files": True, "items": []}, indent=2)); return
        with os.scandir(work_fd) as entries:
            names = []
            for entry in entries:
                names.append(entry.name)
                if len(names) > MAX_WORK_ITEMS: raise ValueError("too many work items")
        for name in sorted(names):
            try: item_fd = os.open(name, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=work_fd)
            except NotADirectoryError: raise ValueError("work item must be a real directory: %s" % name)
            try:
                try: task_fd = _open_at(item_fd, "tasks.md", os.O_RDONLY, max_bytes=MAX_TASK_FILE_BYTES)
                except FileNotFoundError: raise ValueError("work item is missing tasks.md: %s" % name)
                with os.fdopen(task_fd, "r", encoding="utf-8") as handle: text = handle.read(MAX_TASK_FILE_BYTES + 1)
                if len(text.encode("utf-8")) > MAX_TASK_FILE_BYTES: raise ValueError("tasks.md is too large")
                tasks = parse_tasks(text); counts = Counter(task["status"] for task in tasks)
                items.append({"item": name, "tasks": len(tasks), **{status: counts[status] for status in sorted(STATUSES)}})
            finally: os.close(item_fd)
    except OSError as error:
        if error.errno in {20, 40, 62}: raise ValueError("project artifact path must not contain symlinks")
        raise
    finally:
        if work_fd is not None: os.close(work_fd)
        if project_fd is not None: os.close(project_fd)
        os.close(root_fd)
    print(json.dumps({"project_files": True, "items": items}, indent=2))


def parser():
    result = argparse.ArgumentParser(description="Local Parliament of Codex state utility")
    result.add_argument("--root", default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot"); subs = snapshot.add_subparsers(dest="action", required=True)
    create = subs.add_parser("create"); create.add_argument("--label"); create.add_argument("--summary"); create.add_argument("--summary-file"); create.add_argument("--metadata"); create.set_defaults(handler=snapshot_create)
    listing = subs.add_parser("list"); listing.set_defaults(handler=snapshots)
    show = subs.add_parser("show"); show.add_argument("snapshot_id"); show.set_defaults(handler=snapshots)
    prune = subs.add_parser("prune"); prune.add_argument("--keep", type=int, default=20); prune.set_defaults(handler=snapshots)
    telemetry = commands.add_parser("telemetry"); tele = telemetry.add_subparsers(dest="action", required=True)
    rec = tele.add_parser("record"); rec.add_argument("--event", required=True); rec.add_argument("--agent"); rec.add_argument("--outcome"); rec.add_argument("--duration-ms", type=int); rec.add_argument("--tokens", type=int); rec.add_argument("--cost-amount", type=float); rec.add_argument("--cost-currency"); rec.add_argument("--cost-source"); rec.add_argument("--metadata"); rec.set_defaults(handler=record)
    qry = tele.add_parser("query"); qry.add_argument("--event"); qry.add_argument("--agent"); qry.add_argument("--since", default="7d"); qry.add_argument("--group-by", choices=["event", "agent", "outcome"]); qry.add_argument("--limit", type=int, default=100); qry.set_defaults(handler=query)
    prune_tele = tele.add_parser("prune"); prune_tele.add_argument("--older-than", required=True); prune_tele.set_defaults(handler=telemetry_prune)
    clear = tele.add_parser("clear"); clear.add_argument("--confirm", required=True); clear.set_defaults(handler=telemetry_clear)
    metric = commands.add_parser("metrics"); metric.add_argument("--window", default="7d"); metric.add_argument("--by", choices=["event", "agent", "outcome"], default="agent"); metric.set_defaults(handler=metrics)
    status = commands.add_parser("project-status"); status.set_defaults(handler=project_status)
    return result


def main():
    arguments = parser().parse_args()
    try:
        arguments.handler(arguments)
    except (FileNotFoundError, FileExistsError, ValueError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
