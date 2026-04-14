from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MD_LINK_RE = re.compile(r"\(([^)]+?\.md)\)")
BARE_MD_RE = re.compile(r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\\-]+\.md)(?![A-Za-z0-9_./\\-])")
JSON_BLOCK_RE = re.compile(r"```json autorun-metadata\s*(\{.*?\})\s*```", re.DOTALL)
PLANNING_STATE_PATH_RE = re.compile(r"^planningStatePath:\s*(.+?)\s*$", re.MULTILINE)
PLANNING_PROTOCOL_VERSION = "phase-stage-autoplan/codex-v1"


def read_protocol_text(path: str | Path) -> str:
    return Path(path).resolve().read_text(encoding="utf-8")


def read_aclx(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw_line:
            raise ValueError(f"Invalid ACL-X line in {path}: {raw_line}")
        key, value = raw_line.split("=", 1)
        entries[key.strip()] = value.strip()
    return entries


def resolve_optional_path(base: Path, raw_path: str | None) -> str | None:
    if raw_path in (None, "", "none"):
        return None
    candidate = Path(raw_path.strip("`"))
    if candidate.is_absolute():
        return str(candidate.resolve())
    return str((base / candidate).resolve())


def parse_json_value(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, "", "none"):
        return default
    return json.loads(raw_value)


def load_protocol_metadata(path: str | Path) -> dict[str, Any] | None:
    protocol_path = Path(path).resolve()
    planning_state_path = discover_planning_state_path(protocol_path)
    if planning_state_path is not None:
        return load_planning_state_acl(planning_state_path, protocol_path)
    match = JSON_BLOCK_RE.search(read_protocol_text(protocol_path))
    if not match:
        return None
    payload = json.loads(match.group(1))
    return normalize_protocol_metadata(protocol_path, payload)


def discover_planning_state_path(protocol_path: Path) -> Path | None:
    match = PLANNING_STATE_PATH_RE.search(read_protocol_text(protocol_path))
    if match:
        resolved_path = resolve_optional_path(protocol_path.parent, match.group(1).strip())
        if resolved_path is not None:
            candidate = Path(resolved_path)
            if candidate.exists():
                return candidate.resolve()
    sibling = (protocol_path.parent / "planning-state.aclx").resolve()
    if sibling.exists():
        return sibling
    return None


def load_planning_state_acl(planning_state_path: str | Path, protocol_path: str | Path) -> dict[str, Any]:
    aclx_path = Path(planning_state_path).resolve()
    entries = read_aclx(aclx_path)
    if entries.get("protocolVersion") != PLANNING_PROTOCOL_VERSION:
        raise ValueError(
            f"Unsupported planning protocolVersion {entries.get('protocolVersion')!r} in {aclx_path}"
        )
    phases = parse_json_value(entries.get("phase.items"), [])
    normalized_phases: list[dict[str, Any]] = []
    for raw_phase in phases:
        phase = dict(raw_phase)
        phase["path"] = resolve_optional_path(aclx_path.parent, phase.get("path"))
        phase["stageOutlinePath"] = resolve_optional_path(aclx_path.parent, phase.get("stageOutlinePath"))
        phase["stageFiles"] = [
            resolved_path
            for resolved_path in (
                resolve_optional_path(aclx_path.parent, stage_path)
                for stage_path in phase.get("stageFiles", [])
            )
            if resolved_path is not None
        ]
        normalized_phases.append(phase)
    return {
        "runId": entries["runId"],
        "title": entries["title"],
        "projectRoot": entries["project.root"],
        "planningRoot": entries["planning.root"],
        "planningMode": entries["planningMode"],
        "approvalStatus": entries["approval.status"],
        "currentPhaseId": entries["phase.current"],
        "currentExecutablePhaseId": entries.get("phase.executable", entries["phase.current"]),
        "readyPhaseIds": parse_json_value(entries.get("phase.ready"), []),
        "pendingPhaseIds": parse_json_value(entries.get("phase.pending"), []),
        "currentStageQueue": parse_json_value(entries.get("stage.queue"), []),
        "phases": normalized_phases,
        "planningStatePath": str(aclx_path),
        "protocolPath": resolve_optional_path(aclx_path.parent, entries.get("artifacts.protocol"))
        or str(Path(protocol_path).resolve()),
    }


def normalize_protocol_metadata(protocol_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    phases: list[dict[str, Any]] = []
    for raw_phase in payload.get("phases", []):
        phase = dict(raw_phase)
        phase_path = phase.get("path")
        stage_outline_path = phase.get("stageOutlinePath")
        stage_files = phase.get("stageFiles") or []
        phase["path"] = _resolve_protocol_relative(protocol_path, phase_path) if phase_path else None
        phase["stageOutlinePath"] = (
            _resolve_protocol_relative(protocol_path, stage_outline_path)
            if stage_outline_path
            else None
        )
        phase["stageFiles"] = [
            _resolve_protocol_relative(protocol_path, stage_path) for stage_path in stage_files
        ]
        phases.append(phase)
    normalized["phases"] = phases
    normalized["protocolPath"] = str(protocol_path)
    return normalized


def discover_stage_paths(protocol_path: str | Path) -> list[str]:
    resolved_protocol = Path(protocol_path).resolve()
    metadata = load_protocol_metadata(resolved_protocol)
    if metadata is not None:
        ready_stage_paths = flatten_ready_stage_paths(metadata)
        if ready_stage_paths:
            return ready_stage_paths
    return discover_markdown_stage_paths(resolved_protocol)


def discover_markdown_stage_paths(protocol_path: Path) -> list[str]:
    discovered: list[Path] = []
    seen: set[str] = set()
    protocol_dir = protocol_path.parent
    for raw_line in read_protocol_text(protocol_path).splitlines():
        matches = [match.group(1) for match in MD_LINK_RE.finditer(raw_line)]
        matches.extend(match.group(1) for match in BARE_MD_RE.finditer(raw_line))
        for match in matches:
            candidate = (protocol_dir / match).resolve()
            if candidate == protocol_path.resolve():
                continue
            if candidate.suffix.lower() != ".md":
                continue
            if candidate.name in {"phase.md", "stage-outline.md"}:
                continue
            key = str(candidate)
            if key not in seen and candidate.exists():
                seen.add(key)
                discovered.append(candidate)
    return [str(path) for path in discovered]


def flatten_ready_stage_paths(metadata: dict[str, Any]) -> list[str]:
    ready_stage_paths: list[str] = []
    for phase in metadata.get("phases", []):
        if phase.get("detailStatus") != "ready":
            continue
        ready_stage_paths.extend(str(Path(path).resolve()) for path in phase.get("stageFiles", []))
    return ready_stage_paths


def resolve_phase_boundary(protocol_path: str | Path | None, current_stage_path: str | None) -> dict[str, Any] | None:
    if not protocol_path or not current_stage_path:
        return None

    metadata = load_protocol_metadata(protocol_path)
    if metadata is None:
        return None

    current_stage = str(Path(current_stage_path).resolve())
    ready_stage_paths = flatten_ready_stage_paths(metadata)
    if current_stage in ready_stage_paths:
        current_index = ready_stage_paths.index(current_stage)
        if current_index + 1 < len(ready_stage_paths):
            next_stage_path = ready_stage_paths[current_index + 1]
            return {
                "transition": "advance_to_ready_stage",
                "queue_items": ready_stage_paths,
                "queue_cursor": current_index + 1,
                "current_stage_path": next_stage_path,
                "current_stage_id": Path(next_stage_path).stem,
            }

    current_phase_index = _find_phase_index_for_stage(metadata, current_stage)
    if current_phase_index is None:
        return None

    remaining_phases = metadata.get("phases", [])[current_phase_index + 1 :]
    if not remaining_phases:
        return {"transition": "complete_run"}

    next_phase = remaining_phases[0]
    if next_phase.get("detailStatus") == "ready" and next_phase.get("stageFiles"):
        flattened_ready = flatten_ready_stage_paths(metadata)
        next_stage_path = str(Path(next_phase["stageFiles"][0]).resolve())
        if next_stage_path in flattened_ready:
            return {
                "transition": "advance_to_ready_stage",
                "queue_items": flattened_ready,
                "queue_cursor": flattened_ready.index(next_stage_path),
                "current_stage_path": next_stage_path,
                "current_stage_id": Path(next_stage_path).stem,
            }

    return {
        "transition": "block_for_expand",
        "phase_id": next_phase.get("id", "unknown-phase"),
        "phase_title": next_phase.get("title", "Unnamed phase"),
    }


def _resolve_protocol_relative(protocol_path: Path, raw_path: str) -> str:
    return str((protocol_path.parent / raw_path).resolve())


def _find_phase_index_for_stage(metadata: dict[str, Any], current_stage: str) -> int | None:
    for index, phase in enumerate(metadata.get("phases", [])):
        for stage_path in phase.get("stageFiles", []):
            if str(Path(stage_path).resolve()) == current_stage:
                return index
    return None
