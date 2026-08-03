#!/usr/bin/env python3
"""Dependency-free structural and semantic validation for Parliament source/outputs."""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime
from itertools import islice
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.3.0"
MAX_ARTIFACT_BYTES = 2_097_152
MAX_GOVERNED_FILE_BYTES = 1_048_576
MAX_GOVERNED_TOTAL_BYTES = 4_194_304
MAX_GOVERNED_FILES = 100
MAX_PROJECT_ENTRIES = 5000
OPTIONAL_REVIEWERS = {
    "accessibility-reviewer", "architecture-reviewer", "cost-reviewer",
    "documentation-reviewer", "i18n-reviewer", "maintainability-reviewer",
    "performance-reviewer", "privacy-reviewer", "standards-reviewer",
    "testing-reviewer",
}
ACTION_MAP = {
    "council-core": ["ask-council", "summon-council", "summon-specialist"],
    "council-review": ["summon-grumpy-reviewer", "parliament-review"],
    "council-plan": ["plan-project", "roadmap-add-item"],
    "council-scope": ["roadmap-item-scope"], "council-implement": ["implement-task-list"],
    "council-lifecycle": ["project-status", "session-snapshot", "debate-replay", "docs-audit", "env-doctor", "settings-audit", "ci-watch", "fast-track", "parliament-doctor"],
    "council-debate": ["debate-topic", "debate-analytics"],
    "council-decisions": ["adr-new", "adr-supersede", "decision-review"],
    "council-engineering": ["pre-commit-check", "commit-and-push", "format-code", "lint-fix", "run-tests", "security-scan", "clean-imports", "update-dependencies", "dead-code-sweep", "update-docs", "analyse-queries", "git-workflow", "scaffold"],
    "council-quality": ["coverage-audit", "generate-tests", "mutation-test", "test-health", "track-debt", "i18n-audit"],
    "council-release": ["cut-release", "release-notes-draft", "plugin-upgrade"],
    "council-operations": ["telemetry-query", "parliament-metrics", "cost-report", "agent-usage-stats", "incident", "infra-review", "parliament-loop", "parliament-monitor", "parliament-optimize", "parliament-webhook", "changelog-review", "retro"],
    "council-onboard": ["onboard-codebase"],
    "council-discovery": ["list-agents", "explain-agent", "list-commands", "version", "readme", "changelog"],
    "council-plugins": ["plugin-install", "plugin-list"],
}
SCHEMA_CONSUMERS = {
    "council-report.schema.json": "council-implement", "review-report.schema.json": "council-review",
    "snapshot.schema.json": "council-lifecycle", "telemetry.schema.json": "council-operations",
    "debate-record.schema.json": "council-debate", "review-debt.schema.json": "council-lifecycle",
    "project-state.schema.json": "council-plan",
}
TEMPLATE_CONSUMERS = {
    "project-outline.md": "council-plan", "feature-implementation.md": "council-plan", "project-roadmap.md": "council-plan",
    "work-item-spec.md": "council-scope", "tasks.md": "council-scope", "council-report.md": "council-implement",
    "review-report.md": "council-review", "debate-record.md": "council-debate", "review-debt.md": "council-lifecycle", "architectural-decision.md": "council-decisions",
}


class Validation:
    def __init__(self, root):
        self.root = root
        self.errors = []
        self.artifacts = 0

    def require(self, condition, message):
        if not condition:
            self.errors.append(message)

    def relative(self, path):
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def read(self, path, limit=MAX_ARTIFACT_BYTES):
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError("must be a real regular file")
            if path.stat().st_size > limit:
                raise ValueError("file is too large")
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            self.errors.append("cannot read %s: %s" % (self.relative(path), error))
            return ""

    def json(self, path):
        try:
            return json.loads(self.read(path), parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON value")))
        except (ValueError, json.JSONDecodeError) as error:
            self.errors.append("invalid JSON %s: %s" % (self.relative(path), error))
            return None


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("missing closing frontmatter delimiter")
    values = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z][a-z0-9_-]*):\s+(.+)", line)
        if not match or match.group(1) not in {"name", "description"}:
            raise ValueError("unsupported frontmatter line")
        if match.group(1) in values:
            raise ValueError("duplicate frontmatter key")
        values[match.group(1)] = match.group(2).strip()
    if set(values) != {"name", "description"}:
        raise ValueError("frontmatter requires name and description")
    return values, "\n".join(lines[end + 1:])


def declared_actions(body, allowed):
    result = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Action ", "Actions:", "Explicit actions:")) or re.match(r"^-\s+`", stripped):
            result.extend(token for token in re.findall(r"`([a-z][a-z0-9-]+)`", stripped) if token in allowed)
    return result


def _toml_value(raw):
    raw = raw.strip()
    if raw in {"true", "false"}:
        return raw == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith('"') and raw.endswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("invalid quoted string")
    raise ValueError("unsupported TOML value")


def parse_toml_subset(text):
    """Strict parser for this repository's tables, scalars, and multiline strings."""
    result = {}
    current = result
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        index += 1
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        section = re.fullmatch(r"\[([A-Za-z0-9_.-]+)\]", line)
        if section:
            current = result
            for part in section.group(1).split("."):
                if part in current and not isinstance(current[part], dict):
                    raise ValueError("table conflicts with value")
                current = current.setdefault(part, {})
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(.*)", line)
        if not match:
            raise ValueError("unsupported TOML syntax on line %d" % index)
        key, value = match.groups()
        if key in current:
            raise ValueError("duplicate TOML key %s" % key)
        if value == '"""':
            body = []
            while index < len(lines) and lines[index].strip() != '"""':
                body.append(lines[index]); index += 1
            if index >= len(lines):
                raise ValueError("unterminated multiline string")
            index += 1
            current[key] = "\n".join(body)
        else:
            current[key] = _toml_value(value)
    return result


def parse_utc(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def directory_digest(directory):
    digest = hashlib.sha256()
    files = list(islice((path for path in directory.iterdir() if path.name != "project-state.json"), MAX_GOVERNED_FILES + 1))
    if len(files) > MAX_GOVERNED_FILES:
        raise ValueError("too many governed artifact files")
    files.sort()
    total = 0
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("governed artifact must be a real regular file: %s" % path.name)
        before = path.stat()
        if before.st_size > MAX_GOVERNED_FILE_BYTES:
            raise ValueError("governed artifact is too large: %s" % path.name)
        total += before.st_size
        if total > MAX_GOVERNED_TOTAL_BYTES:
            raise ValueError("governed artifact set is too large")
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(relative); digest.update(b"\0")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(path), flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino, info.st_size) != (before.st_dev, before.st_ino, before.st_size):
                raise ValueError("governed artifact changed during hashing: %s" % path.name)
            while True:
                chunk = os.read(fd, 65_536)
                if not chunk: break
                digest.update(chunk)
            after = os.fstat(fd)
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise ValueError("governed artifact changed during hashing: %s" % path.name)
        finally:
            os.close(fd)
        digest.update(b"\0")
    return digest.hexdigest()


def validate_project_state(check, path, value):
    check.artifacts += 1
    required = {"schema_version", "artifact", "status", "revision", "approval"}
    allowed = required | {"invalidated_at", "invalidation_reason"}
    check.require(isinstance(value, dict) and not (set(value) - allowed) and required <= set(value), "%s has invalid project-state keys" % check.relative(path))
    if not isinstance(value, dict): return
    for child in path.parent.iterdir():
        check.require(not child.is_symlink(), "%s artifact directory contains symlink %s" % (check.relative(path), child.name))
    status, revision, approval = value.get("status"), value.get("revision"), value.get("approval")
    check.require(value.get("artifact") == path.parent.name, "%s artifact name does not match directory" % check.relative(path))
    check.require(status in {"draft", "in-review", "approved", "invalidated", "superseded"}, "%s has invalid status" % check.relative(path))
    check.require(isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1, "%s has invalid revision" % check.relative(path))
    if status in {"draft", "in-review"}:
        check.require(approval is None, "%s non-approved draft/review state must have null approval" % check.relative(path))
    if approval is not None:
        coherent = isinstance(approval, dict) and set(approval) == {"approver", "approved_at", "revision", "sha256"}
        check.require(coherent, "%s has invalid approval keys" % check.relative(path))
        if coherent:
            check.require(isinstance(approval.get("approver"), str) and bool(approval["approver"].strip()) and parse_utc(approval.get("approved_at")), "%s has invalid approval identity/time" % check.relative(path))
            check.require(isinstance(approval.get("revision"), int) and not isinstance(approval.get("revision"), bool) and approval["revision"] <= revision, "%s has invalid historical approval revision" % check.relative(path))
            check.require(isinstance(approval.get("sha256"), str) and bool(re.fullmatch(r"[a-f0-9]{64}", approval["sha256"])), "%s has invalid approval digest" % check.relative(path))
    if status == "invalidated":
        check.require(parse_utc(value.get("invalidated_at")) and isinstance(value.get("invalidation_reason"), str) and bool(value.get("invalidation_reason", "").strip()), "%s invalidated state needs time and reason" % check.relative(path))
    if status == "approved":
        check.require(isinstance(approval, dict), "%s approved state needs approval" % check.relative(path))
        if isinstance(approval, dict):
            check.require(approval.get("revision") == revision, "%s approval revision mismatch" % check.relative(path))
            try: current_digest = directory_digest(path.parent)
            except (OSError, ValueError) as error:
                check.errors.append("%s cannot safely hash artifacts: %s" % (check.relative(path), error)); current_digest = None
            check.require(approval.get("sha256") == current_digest, "%s artifact digest is stale" % check.relative(path))


def _nonempty(value): return isinstance(value, str) and bool(value.strip())


def floor_review_errors(value, verdict_key, blockers):
    errors = []
    reviewers = value.get("reviewers") if isinstance(value, dict) else None
    if not isinstance(reviewers, list): return ["reviewers must be an array"]
    valid_status = {"reported", "missing"}; valid_verdict = {"APPROVE", "CHANGES REQUESTED", "INCOMPLETE"}
    for item in reviewers:
        if not isinstance(item, dict) or set(item) != {"role", "status", "verdict", "evidence"} or not _nonempty(item.get("role")) or item.get("status") not in valid_status or item.get("verdict") not in valid_verdict or not _nonempty(item.get("evidence")):
            errors.append("invalid reviewer record")
    for role in ("correctness-reviewer", "security-reviewer"):
        matches = [item for item in reviewers if isinstance(item, dict) and item.get("role") == role]
        if len(matches) != 1: errors.append("requires exactly one %s" % role)
    verdict = value.get(verdict_key)
    if verdict == "APPROVE":
        if any(not isinstance(item, dict) or item.get("status") != "reported" or item.get("verdict") != "APPROVE" for item in reviewers):
            errors.append("APPROVE contradicts reviewer status/verdict")
        if blockers: errors.append("APPROVE has unresolved blocking findings")
    elif verdict == "CHANGES REQUESTED":
        if not blockers and all(isinstance(item, dict) and item.get("status") == "reported" and item.get("verdict") == "APPROVE" for item in reviewers):
            errors.append("CHANGES REQUESTED contradicts reviewer status/verdict and findings")
    elif verdict == "INCOMPLETE":
        if all(isinstance(item, dict) and item.get("status") == "reported" and item.get("verdict") != "INCOMPLETE" for item in reviewers):
            errors.append("INCOMPLETE contradicts complete reviewer reports")
    else:
        errors.append("invalid overall verdict")
    return errors


def review_report_errors(value):
    errors = []
    required = {"schema_version", "review_range", "reviewers", "findings", "validation", "verdict"}
    if not isinstance(value, dict) or set(value) != required or value.get("schema_version") != 1:
        return ["invalid review-report keys/version"]
    review_range = value.get("review_range")
    if not (isinstance(review_range, dict) and set(review_range) == {"base", "head", "included_paths"} and _nonempty(review_range.get("base")) and _nonempty(review_range.get("head")) and isinstance(review_range.get("included_paths"), list) and bool(review_range["included_paths"]) and all(_nonempty(item) for item in review_range["included_paths"])):
        errors.append("invalid review range")
    reviewers = value.get("reviewers", [])
    roles = [item.get("role") for item in reviewers if isinstance(item, dict)]
    if len(roles) != len(set(roles)): errors.append("duplicate reviewer roles")
    severities = {"critical", "high", "medium", "low"}; dispositions = {"open", "resolved", "accepted-risk", "rejected"}
    findings = value.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array"); findings = []
    for item in findings:
        keys = {"id", "severity", "blocking", "disposition", "evidence", "impact", "recommendation", "resolution"}
        if not isinstance(item, dict) or set(item) != keys or not _nonempty(item.get("id")) or item.get("severity") not in severities or type(item.get("blocking")) is not bool or item.get("disposition") not in dispositions or not all(_nonempty(item.get(key)) for key in ("evidence", "impact", "recommendation")) or not isinstance(item.get("resolution"), str):
            errors.append("invalid finding record")
    validation = value.get("validation")
    if not isinstance(validation, list) or not validation:
        errors.append("invalid validation evidence")
    else:
        for item in validation:
            if not isinstance(item, dict) or set(item) != {"command", "result", "evidence"} or not _nonempty(item.get("command")) or item.get("result") not in {"pass", "fail", "not-run"} or not _nonempty(item.get("evidence")):
                errors.append("invalid validation evidence")
    blockers = sum(1 for item in findings if isinstance(item, dict) and item.get("blocking") is True and item.get("disposition") == "open")
    errors.extend(floor_review_errors(value, "verdict", bool(blockers)))
    return errors


def validate_review_report(check, path, value):
    check.artifacts += 1
    for error in review_report_errors(value): check.errors.append("%s: %s" % (check.relative(path), error))


def validate_council_report(check, path, value):
    check.artifacts += 1
    required = {"schema_version", "mode", "review_range", "inventory", "participants", "summary", "validation", "reviewers", "unresolved_blocking_findings", "review_report", "decision", "trade_offs"}
    check.require(isinstance(value, dict) and set(value) == required and value.get("schema_version") == 1, "%s has invalid council-report keys/version" % check.relative(path))
    if not isinstance(value, dict): return
    review_range = value.get("review_range")
    range_ok = isinstance(review_range, dict) and set(review_range) == {"base", "head", "included_paths"} and _nonempty(review_range.get("base")) and _nonempty(review_range.get("head")) and isinstance(review_range.get("included_paths"), list) and bool(review_range["included_paths"]) and all(_nonempty(item) for item in review_range["included_paths"])
    inventory = value.get("inventory")
    inventory_ok = isinstance(inventory, list) and bool(inventory) and all(isinstance(item, dict) and set(item) == {"path", "summary", "reuse_decision"} and _nonempty(item.get("path")) and _nonempty(item.get("summary")) and item.get("reuse_decision") in {"extend", "replace", "none"} for item in inventory)
    participants = value.get("participants")
    validation = value.get("validation"); trade_offs = value.get("trade_offs")
    count = value.get("unresolved_blocking_findings")
    content_ok = value.get("mode") in {"answer", "plan", "implement", "review"} and range_ok and inventory_ok and isinstance(participants, list) and bool(participants) and len(participants) == len(set(participants)) and all(_nonempty(item) for item in participants) and _nonempty(value.get("summary")) and isinstance(validation, list) and bool(validation) and all(_nonempty(item) for item in validation) and isinstance(trade_offs, list) and all(isinstance(item, str) for item in trade_offs) and type(count) is int and count >= 0
    check.require(content_ok, "%s has invalid council report content" % check.relative(path))
    linked = value.get("review_report")
    check.require(_nonempty(linked), "%s review_report must be a nonempty string" % check.relative(path))
    linked_value = None
    if _nonempty(linked):
        lexical_path = check.root / linked
        linked_path = lexical_path.resolve()
        reviews_root = (check.root / ".project-files" / "reports" / "reviews").resolve()
        parts = Path(linked).parts
        symlink_component = Path(linked).is_absolute() or any((check.root.joinpath(*parts[:index])).is_symlink() for index in range(1, len(parts) + 1))
        valid_link = not symlink_component and reviews_root in linked_path.parents and linked_path.suffix == ".json" and linked_path.is_file()
        check.require(valid_link, "%s references a missing/escaping/non-review JSON report" % check.relative(path))
        if valid_link:
            linked_value = check.json(linked_path)
            for error in review_report_errors(linked_value): check.errors.append("%s linked review: %s" % (check.relative(path), error))
    blockers = bool(count) if type(count) is int else True
    for error in floor_review_errors(value, "decision", blockers): check.errors.append("%s: %s" % (check.relative(path), error))
    if isinstance(linked_value, dict):
        linked_blockers = sum(1 for item in linked_value.get("findings", []) if isinstance(item, dict) and item.get("blocking") is True and item.get("disposition") == "open")
        check.require(value.get("decision") == linked_value.get("verdict"), "%s decision disagrees with linked review" % check.relative(path))
        check.require(value.get("review_range") == linked_value.get("review_range"), "%s range disagrees with linked review" % check.relative(path))
        council_floor = {item.get("role"): (item.get("status"), item.get("verdict")) for item in value.get("reviewers", []) if isinstance(item, dict) and item.get("role") in {"correctness-reviewer", "security-reviewer"}}
        review_floor = {item.get("role"): (item.get("status"), item.get("verdict")) for item in linked_value.get("reviewers", []) if isinstance(item, dict) and item.get("role") in {"correctness-reviewer", "security-reviewer"}}
        check.require(council_floor == review_floor, "%s floor reviewers disagree with linked review" % check.relative(path))
        check.require(count == linked_blockers, "%s blocker count disagrees with linked review" % check.relative(path))


def validate_debt(check, path, value):
    check.artifacts += 1
    required = {"schema_version", "id", "change", "skipped_optional_reviews", "owner", "due_at", "status", "follow_up"}
    allowed = required | {"resolution"}
    check.require(isinstance(value, dict) and required <= set(value) and not (set(value) - allowed), "%s has invalid review-debt keys" % check.relative(path))
    if not isinstance(value, dict): return
    valid_text = all(isinstance(value.get(key), str) and bool(value.get(key, "").strip()) for key in ("id", "change", "owner", "follow_up"))
    skipped = value.get("skipped_optional_reviews")
    check.require(value.get("schema_version") == 1 and value.get("status") in {"open", "in-progress", "resolved", "overdue"} and parse_utc(value.get("due_at")) and valid_text and isinstance(skipped, list) and bool(skipped) and all(item in OPTIONAL_REVIEWERS for item in skipped), "%s has invalid review-debt lifecycle or reviewer role" % check.relative(path))
    if value.get("status") == "resolved": check.require(isinstance(value.get("resolution"), str) and bool(value.get("resolution", "").strip()), "%s resolved debt needs resolution" % check.relative(path))
    check.require(path.with_suffix(".md").is_file() and not path.with_suffix(".md").is_symlink(), "%s is missing same-basename Markdown companion" % check.relative(path))


def validate_artifacts(check):
    base = check.root / ".project-files"
    if not base.exists(): return
    if base.is_symlink() or not base.is_dir():
        check.errors.append(".project-files must be a real directory"); return
    entries = list(islice(base.rglob("*"), MAX_PROJECT_ENTRIES + 1))
    if len(entries) > MAX_PROJECT_ENTRIES:
        check.errors.append(".project-files contains too many entries"); return
    for entry in entries:
        check.require(not entry.is_symlink(), ".project-files contains symlink: %s" % check.relative(entry))
    plan = base / "plan"
    if plan.exists() and plan.is_dir() and any(plan.iterdir()):
        check.require((plan / "project-state.json").is_file() and not (plan / "project-state.json").is_symlink(), "populated .project-files/plan requires project-state.json")
    work_items = base / "work-items"
    if work_items.exists() and work_items.is_dir():
        for item in work_items.iterdir():
            if item.is_dir() and not item.is_symlink(): check.require((item / "project-state.json").is_file() and not (item / "project-state.json").is_symlink(), "%s requires project-state.json" % check.relative(item))
    for path in (entry for entry in entries if entry.name == "project-state.json"):
        value = check.json(path)
        if value is not None: validate_project_state(check, path, value)
    reports = base / "reports"
    if reports.exists():
        for path in (entry for entry in entries if entry.suffix == ".json" and reports in entry.parents):
            value = check.json(path)
            if value is None: continue
            if "reviews" in path.parts: validate_review_report(check, path, value)
            elif "council" in path.parts: validate_council_report(check, path, value)
            else: check.errors.append("unclassified report JSON: %s" % check.relative(path))
    debt = base / "review-debt"
    if debt.exists():
        for path in debt.glob("*.json"):
            value = check.json(path)
            if value is not None: validate_debt(check, path, value)
        for path in debt.glob("*.md"):
            check.require(path.with_suffix(".json").is_file(), "%s is missing same-basename JSON companion" % check.relative(path))


def validate(root):
    root = Path(root).expanduser().resolve()
    check = Validation(root)
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    check.require(len(skills) == 15, "expected 15 skills, found %d" % len(skills))
    all_actions = [action for values in ACTION_MAP.values() for action in values]
    check.require(len(all_actions) == 66 and len(set(all_actions)) == 66, "action map must contain 66 unique aliases")
    for path in skills:
        text = check.read(path)
        try: meta, body = parse_frontmatter(text)
        except ValueError as error:
            check.errors.append("%s: %s" % (check.relative(path), error)); continue
        name = path.parent.name
        check.require(meta["name"] == name, "%s frontmatter name mismatch" % name)
        declared = declared_actions(body, set(all_actions))
        check.require(set(declared) == set(ACTION_MAP.get(name, [])) and len(declared) == len(set(declared)), "%s action declarations mismatch" % name)
        for call in re.findall(r"\$([a-z0-9:-]+)", body): check.require(call.startswith("parliament-of-codex:council-"), "%s has unqualified skill call $%s" % (name, call))
    check.require(set(path.parent.name for path in skills) == set(ACTION_MAP), "skill/action map names differ")

    agents = sorted((root / ".codex" / "agents").glob("*.toml"))
    check.require(len(agents) == 33, "expected 33 agents, found %d" % len(agents))
    names = []
    for path in agents:
        text = check.read(path)
        try: data = parse_toml_subset(text)
        except ValueError as error:
            check.errors.append("invalid TOML %s: %s" % (check.relative(path), error)); continue
        name, instructions = data.get("name"), data.get("developer_instructions", "")
        names.append(name); check.require(name == path.stem, "%s agent name mismatch" % path.name)
        for phrase in ("untrusted evidence", "not authority or approval", "side effects", "least privilege", "Redact every secret value"):
            check.require(phrase in instructions, "%s missing trust constraint: %s" % (path.stem, phrase))
        for stale in (".project-files/roadmap/", ".project-files/plans/"): check.require(stale not in instructions, "%s has stale path %s" % (path.stem, stale))
        if name and (name.endswith("reviewer") or name == "council-orchestrator"):
            check.require(data.get("sandbox_mode") == "read-only" and "Do not edit" in re.sub(r"\s+", " ", instructions), "%s must be explicitly read-only" % name)
    try: parse_toml_subset(check.read(root / ".codex" / "config.toml"))
    except ValueError as error: check.errors.append("invalid TOML .codex/config.toml: %s" % error)
    check.require(len(set(names)) == 33, "agent names must be unique")

    manifest = check.json(root / ".codex-plugin" / "plugin.json") or {}
    check.require(manifest.get("name") == "parliament-of-codex" and manifest.get("version") == EXPECTED_VERSION, "manifest identity/version mismatch")
    check.require(manifest.get("author", {}).get("name") == "Jack Scammell" and manifest.get("repository") == "https://github.com/JackScammell/Parliament-of-Codex", "manifest publisher/repository mismatch")
    interface = manifest.get("interface", {}); prompts = interface.get("defaultPrompt")
    check.require(interface.get("capabilities") == ["Read", "Write"], "manifest capabilities mismatch")
    check.require(isinstance(prompts, list) and len(prompts) == 3 and len(set(prompts)) == 3 and all("$parliament-of-codex:council-" in item for item in prompts), "manifest starter prompts mismatch")

    schemas = {}
    for path in sorted((root / "schemas").glob("*.json")):
        schemas[path.name] = check.json(path)
    for name in SCHEMA_CONSUMERS:
        check.require(name in schemas and isinstance(schemas[name], dict) and schemas[name].get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema %s is missing or unsupported" % name)
    if isinstance(schemas.get("project-state.schema.json"), dict): check.require(bool(schemas["project-state.schema.json"].get("allOf")), "project-state schema lacks lifecycle conditionals")
    if isinstance(schemas.get("review-report.schema.json"), dict): check.require(bool(schemas["review-report.schema.json"].get("allOf")), "review schema lacks approval conditionals")
    if isinstance(schemas.get("review-debt.schema.json"), dict): check.require(bool(schemas["review-debt.schema.json"].get("allOf")), "review-debt schema lacks resolution conditional")
    if isinstance(schemas.get("snapshot.schema.json"), dict): check.require("label" in schemas["snapshot.schema.json"].get("required", []), "snapshot schema must require label")
    if isinstance(schemas.get("telemetry.schema.json"), dict): check.require(set(schemas["telemetry.schema.json"].get("required", [])) == {"schema_version", "timestamp", "event", "agent", "outcome", "duration_ms", "tokens", "cost", "metadata"}, "telemetry schema required keys mismatch")
    for name, consumer in SCHEMA_CONSUMERS.items(): check.require(name in check.read(root / "docs" / "ARTIFACT_CONTRACT.md") or name in check.read(root / "skills" / consumer / "SKILL.md"), "schema %s has no documented consumer" % name)
    for name, consumer in TEMPLATE_CONSUMERS.items(): check.require((root / "templates" / name).exists() and name in check.read(root / "skills" / consumer / "SKILL.md"), "template %s has no workflow consumer" % name)

    parity = check.read(root / "docs" / "FEATURE_PARITY.md")
    rows = re.findall(r"^\| `([^`]+)` \| `\$([^`]+)` \| `([^`]+)` \| Supported \|$", parity, re.MULTILINE)
    check.require(len(rows) == 66 and {row[0] for row in rows} == set(all_actions), "feature parity must map 66 unique aliases")
    check.require(all(row[0] == row[2] and row[1].startswith("parliament-of-codex:council-") for row in rows), "feature parity rows must be qualified and explicit")
    markdown = list(root.glob("*.md")) + list((root / "docs").glob("*.md")) + list((root / "skills").glob("*/SKILL.md")) + list((root / "templates").glob("*.md"))
    link_pattern = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)]+)\)")
    for path in markdown:
        text = check.read(path)
        for target in link_pattern.findall(text):
            clean = target.split("#", 1)[0]
            if clean:
                resolved = (path.parent / clean).resolve()
                check.require(resolved.exists() and (resolved == root or root in resolved.parents), "broken or escaping link %s -> %s" % (check.relative(path), target))
    corpus_paths = [path for path in markdown if path.name != "MIGRATION_0_3.md"] + [root / ".gitignore", root / ".codex-plugin" / "plugin.json"]
    corpus = "\n".join(check.read(path) for path in corpus_paths)
    for stale in ("$council-", ".project-files/roadmap/", ".project-files/plans/", "docs/getting_started/", "Local developer", ".project-files/.telemetry/"):
        check.require(stale not in corpus, "stale phrase/path remains: %s" % stale)
    check.require("/Users/" not in check.read(root / "docs" / "VALIDATION.md"), "validation docs contain maintainer absolute path")
    validate_artifacts(check)
    return check


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", default=DEFAULT_ROOT)
    args = parser.parse_args(); check = validate(args.root)
    if check.errors:
        for error in check.errors: print("ERROR: " + error, file=sys.stderr)
        print("validation failed: %d error(s)" % len(check.errors), file=sys.stderr); return 1
    artifact_note = "%d artifact JSON record(s) validated" % check.artifacts if check.artifacts else "no project artifact JSON present; contract fixtures are exercised by tests"
    print("validation passed: 15 skills, 33 agents, 66 structurally declared aliases; " + artifact_note)
    return 0


if __name__ == "__main__": raise SystemExit(main())
