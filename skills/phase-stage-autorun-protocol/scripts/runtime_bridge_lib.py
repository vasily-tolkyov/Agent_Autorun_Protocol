from __future__ import annotations

import contextlib
import json
import os
import re
import tempfile
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"

PLACEHOLDER_RE = re.compile(r"{{([a-zA-Z0-9_]+)}}")
CURRENT_PROTOCOL_VERSION = "phase-stage-autorun/codex-v1"
SUPPORTED_PROTOCOL_VERSIONS = {CURRENT_PROTOCOL_VERSION}

if os.name == "nt":
    import msvcrt
else:
    import fcntl

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temp_file = Path(temp_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_file, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_file.unlink()


def render_template_file(template_name: str, mapping: dict[str, Any]) -> str:
    template_path = TEMPLATES_DIR / template_name
    content = read_text(template_path)
    rendered = content
    for key, value in mapping.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", stringify(value))
    unresolved = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    if unresolved:
        raise ValueError(
            f"Unresolved placeholders in {template_name}: {', '.join(unresolved)}"
        )
    return rendered


def stringify(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return json.dumps([stringify_scalar(item) for item in value])
    return str(value)


def stringify_scalar(value: Any) -> Any:
    if value is None:
        return "none"
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, bool):
        return value
    return value


def read_aclx(path: Path) -> OrderedDict[str, str]:
    entries: OrderedDict[str, str] = OrderedDict()
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid ACL-X line in {path}: {raw_line}")
        key, value = raw_line.split("=", 1)
        entries[key.strip()] = value.strip()
    return entries


def validate_protocol_version(entries: OrderedDict[str, str], source_path: Path) -> str:
    version = entries.get("protocolVersion")
    if version is None:
        raise ValueError(f"Missing protocolVersion in {source_path}")
    if version not in SUPPORTED_PROTOCOL_VERSIONS:
        raise ValueError(
            f"Unsupported protocolVersion {version!r} in {source_path}. "
            f"Supported versions: {', '.join(sorted(SUPPORTED_PROTOCOL_VERSIONS))}"
        )
    return version


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


def normalize_path(value: str | Path | None) -> str | None:
    if value in (None, "", "none"):
        return None
    return str(Path(value).resolve())


def derive_stage_id(stage_path: str | None, fallback: str | None = None) -> str:
    if stage_path:
        return Path(stage_path).stem
    if fallback:
        return fallback
    return "none"


def ordered_stage_lines(stage_paths: list[str]) -> str:
    return "\n".join(f"{index}. {path}" for index, path in enumerate(stage_paths, start=1))


def parse_queue_items(raw_value: str) -> list[str]:
    value = raw_value.strip()
    if not value or value == "none":
        return []
    if value.startswith("["):
        items = json.loads(value)
        return [str(item) for item in items]
    return [item.strip() for item in value.split(",") if item.strip()]


def state_from_package_entries(root: Path, entries: OrderedDict[str, str]) -> dict[str, Any]:
    validate_protocol_version(entries, root / "run-package.aclx")
    queue_items = parse_queue_items(entries["queue.items"])
    queue_cursor = int(entries["queue.cursor"])
    current_stage_path = (
        queue_items[queue_cursor] if 0 <= queue_cursor < len(queue_items) else None
    )
    status_path = normalize_path(entries.get("artifacts.status"))
    controlling_protocol_path = normalize_path(entries.get("artifacts.controllingProtocol"))
    return {
        "run_root": root,
        "package_path": root / "run-package.aclx",
        "goal_path": Path(entries["artifacts.goal"]).resolve(),
        "queue_path": Path(entries["artifacts.queue"]).resolve(),
        "status_path": Path(status_path) if status_path else None,
        "controlling_protocol_path": controlling_protocol_path,
        "checkpoints_dir": Path(entries["artifacts.checkpoints"]).resolve(),
        "snapshots_dir": Path(entries["artifacts.snapshots"]).resolve(),
        "run_id": entries["runId"],
        "run_title": entries["title"],
        "created_at": entries["createdAt"],
        "queue_items": queue_items,
        "queue_cursor": queue_cursor,
        "current_stage_id": entries["stage.current"],
        "current_stage_path": current_stage_path,
        "stage_state": entries["stage.state"],
        "next_action": entries["stage.next"],
        "blocker": entries["stage.blocker"],
        "audit_pass_streak": int(entries["audit.passStreak"]),
        "audit_fail_streak": int(entries["audit.failStreak"]),
        "latest_verification": entries["verify.latest"],
        "resume_point": entries["resume.point"],
        "protocol_version": entries["protocolVersion"],
    }


def load_runtime_state(run_root: str | Path) -> dict[str, Any]:
    root = Path(run_root).resolve()
    package_path = root / "run-package.aclx"
    entries = read_aclx(package_path)
    state = state_from_package_entries(root, entries)
    state["package_path"] = package_path
    return state


def initialize_state(
    run_root: str | Path,
    run_id: str,
    run_title: str,
    created_at: str,
    stage_paths: list[str],
    controlling_protocol_path: str | None = None,
    current_stage_id: str | None = None,
    stage_state: str = "planned",
    next_action: str = "read_stage_plan",
    blocker: str = "none",
    audit_pass_streak: int = 0,
    audit_fail_streak: int = 0,
    latest_verification: str = "none",
    resume_point: str = "none",
) -> dict[str, Any]:
    root = Path(run_root).resolve()
    normalized_stages = [str(Path(path).resolve()) for path in stage_paths]
    queue_cursor = 0
    current_stage_path = normalized_stages[0] if normalized_stages else None
    current_id = derive_stage_id(current_stage_path, current_stage_id)

    return {
        "run_root": root,
        "package_path": root / "run-package.aclx",
        "goal_path": root / "goal.md",
        "queue_path": root / "queue.md",
        "status_path": root / "status.json",
        "controlling_protocol_path": normalize_path(controlling_protocol_path),
        "checkpoints_dir": root / "checkpoints",
        "snapshots_dir": root / "snapshots",
        "run_id": run_id,
        "run_title": run_title,
        "created_at": created_at,
        "queue_items": normalized_stages,
        "queue_cursor": queue_cursor,
        "current_stage_id": current_id,
        "current_stage_path": current_stage_path,
        "stage_state": stage_state,
        "next_action": next_action,
        "blocker": blocker,
        "audit_pass_streak": audit_pass_streak,
        "audit_fail_streak": audit_fail_streak,
        "latest_verification": latest_verification,
        "resume_point": resume_point,
        "protocol_version": CURRENT_PROTOCOL_VERSION,
    }


def persist_runtime_state(
    state: dict[str, Any],
    *,
    controlling_protocol_path: str | None = None,
    queue_source: str | None = None,
    write_status: bool | None = None,
) -> None:
    state["run_root"].mkdir(parents=True, exist_ok=True)
    state["checkpoints_dir"].mkdir(parents=True, exist_ok=True)
    state["snapshots_dir"].mkdir(parents=True, exist_ok=True)

    package_content = render_template_file(
        "run-package.template.aclx",
        {
            "run_id": state["run_id"],
            "run_title": state["run_title"],
            "created_at": state["created_at"],
            "goal_path": state["goal_path"],
            "queue_path": state["queue_path"],
            "status_path": state["status_path"] or "none",
            "controlling_protocol_path": state.get("controlling_protocol_path") or "none",
            "checkpoints_dir": state["checkpoints_dir"],
            "snapshots_dir": state["snapshots_dir"],
            "queue_items_json": json.dumps(state["queue_items"], ensure_ascii=True),
            "queue_cursor": state["queue_cursor"],
            "current_stage_id": state["current_stage_id"],
            "stage_state": state["stage_state"],
            "next_action": state["next_action"],
            "blocker": state["blocker"],
            "audit_pass_streak": state["audit_pass_streak"],
            "audit_fail_streak": state["audit_fail_streak"],
            "latest_verification": state["latest_verification"],
            "resume_point": state["resume_point"],
        },
    )
    write_text(state["package_path"], package_content)

    queue_content = render_template_file(
        "queue.template.md",
        {
            "run_id": state["run_id"],
            "ordered_stage_lines": ordered_stage_lines(state["queue_items"]),
            "queue_cursor": state["queue_cursor"],
            "current_stage_id": state["current_stage_id"],
            "current_stage_path": state["current_stage_path"] or "none",
            "stage_state": state["stage_state"],
        },
    )
    write_text(state["queue_path"], queue_content)

    if controlling_protocol_path is not None or queue_source is not None or not state["goal_path"].exists():
        goal_content = render_template_file(
            "goal.template.md",
            {
                "run_title": state["run_title"],
                "controlling_protocol_path": controlling_protocol_path or "none",
                "queue_source": queue_source or "none",
            },
        )
        write_text(state["goal_path"], goal_content)

    should_write_status = write_status
    if should_write_status is None:
        should_write_status = state["status_path"] is not None
    if should_write_status and state["status_path"] is not None:
        status_value = "blocked" if state["blocker"] != "none" else "active"
        if (
            state["queue_items"]
            and state["queue_cursor"] == len(state["queue_items"]) - 1
            and state["stage_state"] == "done"
        ):
            status_value = "completed"
        write_json(
            state["status_path"],
            {
                "runId": state["run_id"],
                "status": status_value,
                "currentStageId": state["current_stage_id"],
                "stageState": state["stage_state"],
                "nextAction": state["next_action"],
                "blocker": state["blocker"],
                "resumePoint": state["resume_point"],
                "updatedAt": now_iso(),
            },
        )


def write_checkpoint(state: dict[str, Any], checkpoint_id: str, reason: str) -> Path:
    checkpoint_path = state["checkpoints_dir"] / f"{checkpoint_id}.aclx"
    state["resume_point"] = str(checkpoint_path.resolve())
    checkpoint_content = render_template_file(
        "checkpoint-delta.template.aclx",
        {
            "run_id": state["run_id"],
            "checkpoint_id": checkpoint_id,
            "created_at": now_iso(),
            "run_package_path": state["package_path"],
            "resume_point": checkpoint_path.resolve(),
            "current_stage_id": state["current_stage_id"],
            "stage_state": state["stage_state"],
            "next_action": state["next_action"],
            "blocker": state["blocker"],
            "audit_pass_streak": state["audit_pass_streak"],
            "audit_fail_streak": state["audit_fail_streak"],
            "latest_verification": state["latest_verification"],
            "checkpoint_reason": reason,
        },
    )
    write_text(checkpoint_path, checkpoint_content)
    return checkpoint_path.resolve()


def latest_checkpoint_path(checkpoints_dir: Path) -> Path | None:
    files = sorted(checkpoints_dir.glob("*.aclx"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def write_snapshot(state: dict[str, Any], snapshot_id: str, reason: str) -> Path:
    snapshot_path = state["snapshots_dir"] / f"{snapshot_id}.aclx"
    snapshot_content = render_template_file(
        "snapshot-state.template.aclx",
        {
            "snapshot_id": snapshot_id,
            "snapshot_reason": reason,
            "snapshot_created_at": now_iso(),
            "run_id": state["run_id"],
            "run_title": state["run_title"],
            "run_created_at": state["created_at"],
            "source_package_path": state["package_path"],
            "goal_path": state["goal_path"],
            "queue_path": state["queue_path"],
            "status_path": state["status_path"] or "none",
            "controlling_protocol_path": state.get("controlling_protocol_path") or "none",
            "checkpoints_dir": state["checkpoints_dir"],
            "snapshots_dir": state["snapshots_dir"],
            "queue_items_json": json.dumps(state["queue_items"], ensure_ascii=True),
            "queue_cursor": state["queue_cursor"],
            "current_stage_id": state["current_stage_id"],
            "stage_state": state["stage_state"],
            "next_action": state["next_action"],
            "blocker": state["blocker"],
            "audit_pass_streak": state["audit_pass_streak"],
            "audit_fail_streak": state["audit_fail_streak"],
            "latest_verification": state["latest_verification"],
            "resume_point": state["resume_point"],
        },
    )
    write_text(snapshot_path, snapshot_content)
    return snapshot_path.resolve()


def latest_snapshot_path(snapshots_dir: Path) -> Path | None:
    files = sorted(snapshots_dir.glob("*.aclx"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def apply_checkpoint_delta(state: dict[str, Any], checkpoint_entries: OrderedDict[str, str]) -> dict[str, Any]:
    validate_protocol_version(checkpoint_entries, state["run_root"] / "checkpoints")
    updated = dict(state)
    mapping = {
        "delta.stage.current": "current_stage_id",
        "delta.stage.state": "stage_state",
        "delta.stage.next": "next_action",
        "delta.stage.blocker": "blocker",
        "delta.audit.passStreak": "audit_pass_streak",
        "delta.audit.failStreak": "audit_fail_streak",
        "delta.verify.latest": "latest_verification",
    }
    for source_key, target_key in mapping.items():
        if source_key in checkpoint_entries:
            value = checkpoint_entries[source_key]
            if target_key in ("audit_pass_streak", "audit_fail_streak"):
                updated[target_key] = int(value)
            else:
                updated[target_key] = value
    if "resumePoint" in checkpoint_entries:
        updated["resume_point"] = checkpoint_entries["resumePoint"]
    updated["current_stage_path"] = stage_path_for_cursor(
        updated["queue_items"], updated["queue_cursor"]
    )
    return updated


def apply_runtime_snapshot(run_root: str | Path, snapshot_entries: OrderedDict[str, str]) -> dict[str, Any]:
    root = Path(run_root).resolve()
    validate_protocol_version(snapshot_entries, root / "snapshots")
    package_like_entries = OrderedDict(
        (key, value)
        for key, value in snapshot_entries.items()
        if not key.startswith("snapshot.")
        and key not in {"kind", "sourcePackage", "createdAtSnapshot"}
    )
    state = state_from_package_entries(root, package_like_entries)
    state["package_path"] = root / "run-package.aclx"
    return state


def stage_path_for_cursor(stage_paths: list[str], queue_cursor: int) -> str | None:
    if 0 <= queue_cursor < len(stage_paths):
        return stage_paths[queue_cursor]
    return None


def update_stage_pointer(state: dict[str, Any]) -> None:
    state["current_stage_path"] = stage_path_for_cursor(
        state["queue_items"], state["queue_cursor"]
    )
    if state["current_stage_path"]:
        state["current_stage_id"] = derive_stage_id(
            state["current_stage_path"], state["current_stage_id"]
        )


def migrate_artifact_version(entries: OrderedDict[str, str]) -> tuple[OrderedDict[str, str], bool]:
    version = entries.get("protocolVersion")
    if version is None:
        raise ValueError("Artifact is missing protocolVersion")
    if version == CURRENT_PROTOCOL_VERSION:
        return entries, False
    raise ValueError(
        f"Unsupported protocolVersion {version!r}. "
        f"Only {CURRENT_PROTOCOL_VERSION!r} is currently supported."
    )


@contextlib.contextmanager
def runtime_lock(run_root: str | Path, timeout_s: float = 30.0, poll_interval_s: float = 0.1):
    root = Path(run_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".runtime.lock"
    with open(lock_path, "a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b" ")
            handle.flush()
        start = time.monotonic()
        while True:
            try:
                _lock_file(handle)
                handle.seek(0)
                handle.truncate()
                handle.write(
                    json.dumps(
                        {"pid": os.getpid(), "acquiredAt": now_iso()},
                        ensure_ascii=True,
                    ).encode("utf-8")
                )
                handle.flush()
                break
            except OSError:
                if time.monotonic() - start >= timeout_s:
                    raise TimeoutError(f"Timed out acquiring runtime lock: {lock_path}")
                time.sleep(poll_interval_s)
        try:
            yield lock_path
        finally:
            handle.seek(0)
            handle.truncate()
            handle.flush()
            _unlock_file(handle)


def _lock_file(handle: Any) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(handle: Any) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def export_state(
    state: dict[str, Any],
    checkpoint_path: Path | None = None,
    snapshot_path: Path | None = None,
) -> dict[str, Any]:
    payload = {
        "runId": state["run_id"],
        "runRoot": str(state["run_root"]),
        "packagePath": str(state["package_path"]),
        "goalPath": str(state["goal_path"]),
        "queuePath": str(state["queue_path"]),
        "statusPath": str(state["status_path"]) if state["status_path"] else None,
        "controllingProtocolPath": state.get("controlling_protocol_path"),
        "checkpointsDir": str(state["checkpoints_dir"]),
        "snapshotsDir": str(state["snapshots_dir"]),
        "queueCursor": state["queue_cursor"],
        "queueItems": state["queue_items"],
        "currentStageId": state["current_stage_id"],
        "currentStagePath": state["current_stage_path"],
        "stageState": state["stage_state"],
        "nextAction": state["next_action"],
        "blocker": state["blocker"],
        "auditPassStreak": state["audit_pass_streak"],
        "auditFailStreak": state["audit_fail_streak"],
        "latestVerification": state["latest_verification"],
        "resumePoint": state["resume_point"],
    }
    if checkpoint_path is not None:
        payload["checkpointPath"] = str(checkpoint_path)
    if snapshot_path is not None:
        payload["snapshotPath"] = str(snapshot_path)
    return payload
