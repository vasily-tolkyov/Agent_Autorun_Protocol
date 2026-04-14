from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from autorun_protocol import discover_stage_paths as discover_protocol_stage_paths
from autorun_protocol import resolve_phase_boundary
from runtime_bridge_lib import (
    apply_runtime_snapshot,
    export_state,
    initialize_state,
    latest_checkpoint_path,
    latest_snapshot_path,
    load_runtime_state,
    migrate_artifact_version,
    now_iso,
    persist_runtime_state,
    read_aclx,
    apply_checkpoint_delta,
    runtime_lock,
    timestamp_slug,
    update_stage_pointer,
    write_checkpoint,
    write_snapshot,
)
EVENT_CHOICES = [
    "implementation-started",
    "build-verified",
    "protocol-reread-1",
    "audit-started",
    "critic-pass",
    "critic-fail",
    "repair-started",
    "repair-verified",
    "protocol-reread-2",
    "stage-done",
    "blocker",
    "blocker-cleared",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Top-level runtime driver for the phase/stage autorun ACL-X protocol."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser(
        "bootstrap", help="Create the runtime bridge and initialize the first stage."
    )
    bootstrap.add_argument("--run-root", required=True)
    bootstrap.add_argument("--run-id", required=True)
    bootstrap.add_argument("--title", required=True)
    bootstrap.add_argument("--controlling-protocol-path", required=True)
    bootstrap.add_argument(
        "--queue-source",
        help="Optional explicit queue source description. Defaults to the controlling protocol path.",
    )
    bootstrap.add_argument("--stage", action="append", dest="stages")
    bootstrap.add_argument(
        "--stage-glob",
        help="Optional glob relative to the protocol directory for stage plan discovery.",
    )
    bootstrap.add_argument("--no-status", action="store_true")
    bootstrap.add_argument("--write-snapshot", action="store_true")
    bootstrap.add_argument("--snapshot-id")
    bootstrap.add_argument("--snapshot-reason", default="bootstrap")

    event = subparsers.add_parser(
        "event", help="Apply a protocol event and persist the updated runtime state."
    )
    event.add_argument("--run-root", required=True)
    event.add_argument("--event", choices=EVENT_CHOICES, required=True)
    event.add_argument("--latest-verification")
    event.add_argument("--blocker")
    event.add_argument("--next-action")
    event.add_argument("--required-pass-streak", type=int, default=5)
    event.add_argument("--fail-limit", type=int, default=10)
    event.add_argument("--write-checkpoint", action="store_true")
    event.add_argument("--checkpoint-id")
    event.add_argument("--checkpoint-reason")
    event.add_argument("--write-snapshot", action="store_true")
    event.add_argument("--snapshot-id")
    event.add_argument("--snapshot-reason")

    status = subparsers.add_parser("status", help="Print the current runtime state.")
    status.add_argument("--run-root", required=True)

    resume = subparsers.add_parser(
        "resume", help="Load the latest checkpoint and optionally reapply it to the runtime bridge."
    )
    resume.add_argument("--run-root", required=True)
    resume.add_argument("--checkpoint")
    resume.add_argument("--snapshot")
    resume.add_argument("--prefer-snapshot", action="store_true")
    resume.add_argument("--apply", action="store_true")

    migrate = subparsers.add_parser(
        "migrate",
        help="Validate or migrate runtime artifacts to the current protocol version.",
    )
    migrate.add_argument("--run-root", required=True)
    migrate.add_argument("--apply", action="store_true")

    return parser


def discover_stage_paths(
    controlling_protocol_path: Path,
    explicit_stages: list[str] | None,
    stage_glob: str | None,
) -> list[str]:
    if explicit_stages:
        return [str(Path(path).resolve()) for path in explicit_stages]

    if stage_glob:
        discovered = sorted(controlling_protocol_path.parent.glob(stage_glob))
        stage_paths = [str(path.resolve()) for path in discovered if path.exists()]
    else:
        stage_paths = discover_protocol_stage_paths(controlling_protocol_path)
    if not stage_paths:
        raise SystemExit(
            "No stage plans found. Pass --stage explicitly or provide a protocol file that references .md stage files."
        )
    return stage_paths


def bootstrap_runtime(args: argparse.Namespace) -> dict[str, Any]:
    controlling_protocol_path = Path(args.controlling_protocol_path).resolve()
    stage_paths = discover_stage_paths(controlling_protocol_path, args.stages, args.stage_glob)
    queue_source = args.queue_source or str(controlling_protocol_path)

    with runtime_lock(args.run_root):
        state = initialize_state(
            run_root=Path(args.run_root).resolve(),
            run_id=args.run_id,
            run_title=args.title,
            created_at=now_iso(),
            stage_paths=stage_paths,
            controlling_protocol_path=str(controlling_protocol_path),
        )
        if args.no_status:
            state["status_path"] = None

        persist_runtime_state(
            state,
            controlling_protocol_path=str(controlling_protocol_path),
            queue_source=queue_source,
            write_status=not args.no_status,
        )
        snapshot_path = None
        if args.write_snapshot:
            snapshot_path = write_snapshot(
                state,
                args.snapshot_id or f"{args.run_id}-bootstrap",
                args.snapshot_reason,
            )
        return export_state(state, snapshot_path=snapshot_path)


def reduce_event(state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    updated = dict(state)
    event = args.event
    verification = args.latest_verification
    blocker = args.blocker
    required_pass_streak = args.required_pass_streak
    fail_limit = args.fail_limit

    if event == "implementation-started":
        updated["stage_state"] = "implementing"
        updated["next_action"] = args.next_action or "build_stage"
    elif event == "build-verified":
        updated["stage_state"] = "build_verified"
        updated["next_action"] = args.next_action or "protocol_reread_1"
        if verification:
            updated["latest_verification"] = verification
    elif event == "protocol-reread-1":
        updated["stage_state"] = "protocol_reread_1"
        updated["next_action"] = args.next_action or "start_audit"
    elif event == "audit-started":
        updated["stage_state"] = "audit_running"
        updated["next_action"] = args.next_action or "await_audit_result"
    elif event == "critic-pass":
        updated["audit_pass_streak"] += 1
        updated["audit_fail_streak"] = 0
        if verification:
            updated["latest_verification"] = verification
        if updated["audit_pass_streak"] >= required_pass_streak:
            updated["stage_state"] = "post_repair_verified"
            updated["next_action"] = args.next_action or "protocol_reread_2"
        else:
            updated["stage_state"] = "audit_running"
            updated["next_action"] = args.next_action or "continue_audit"
    elif event == "critic-fail":
        updated["audit_pass_streak"] = 0
        updated["audit_fail_streak"] += 1
        updated["stage_state"] = "repairing"
        updated["next_action"] = args.next_action or "request_refiner_plan"
        if verification:
            updated["latest_verification"] = verification
        if updated["audit_fail_streak"] >= fail_limit:
            updated["stage_state"] = "blocked"
            updated["blocker"] = blocker or "unresolved_contract"
            updated["next_action"] = "report_blocker"
    elif event == "repair-started":
        updated["stage_state"] = "repairing"
        updated["next_action"] = args.next_action or "generator_repair_round"
    elif event == "repair-verified":
        updated["stage_state"] = "post_repair_verified"
        updated["next_action"] = args.next_action or "protocol_reread_2"
        if verification:
            updated["latest_verification"] = verification
    elif event == "protocol-reread-2":
        updated["stage_state"] = "protocol_reread_2"
        updated["next_action"] = args.next_action or "mark_stage_done"
    elif event == "stage-done":
        updated["stage_state"] = "done"
        updated["blocker"] = "none"
        if updated["queue_cursor"] < len(updated["queue_items"]) - 1:
            updated["queue_cursor"] += 1
            update_stage_pointer(updated)
            updated["stage_state"] = "planned"
            updated["next_action"] = "read_stage_plan"
            updated["audit_pass_streak"] = 0
            updated["audit_fail_streak"] = 0
            updated["latest_verification"] = "none"
        else:
            boundary = resolve_phase_boundary(
                updated.get("controlling_protocol_path"),
                updated.get("current_stage_path"),
            )
            if boundary and boundary.get("transition") == "advance_to_ready_stage":
                updated["queue_items"] = boundary["queue_items"]
                updated["queue_cursor"] = boundary["queue_cursor"]
                updated["current_stage_path"] = boundary["current_stage_path"]
                updated["current_stage_id"] = boundary["current_stage_id"]
                updated["stage_state"] = "planned"
                updated["next_action"] = "read_stage_plan"
                updated["audit_pass_streak"] = 0
                updated["audit_fail_streak"] = 0
                updated["latest_verification"] = "none"
            elif boundary and boundary.get("transition") == "block_for_expand":
                updated["stage_state"] = "blocked"
                updated["blocker"] = "missing_plan"
                updated["next_action"] = "expand_phase_plan"
                updated["latest_verification"] = boundary.get("phase_id", "missing-plan")
            else:
                updated["next_action"] = "complete_run"
    elif event == "blocker":
        updated["stage_state"] = "blocked"
        updated["blocker"] = blocker or updated["blocker"] or "unresolved_contract"
        updated["next_action"] = args.next_action or "report_blocker"
    elif event == "blocker-cleared":
        updated["blocker"] = "none"
        updated["stage_state"] = "planned"
        updated["next_action"] = args.next_action or "read_stage_plan"
    else:
        raise SystemExit(f"Unsupported event: {event}")

    if event not in ("blocker",) and updated["stage_state"] != "blocked" and not blocker:
        updated["blocker"] = "none"
    elif blocker:
        updated["blocker"] = blocker

    return updated


def apply_event(args: argparse.Namespace) -> dict[str, Any]:
    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)
        updated = reduce_event(state, args)
        checkpoint_path = None
        if args.write_checkpoint:
            checkpoint_reason = args.checkpoint_reason or args.event
            checkpoint_path = write_checkpoint(
                updated,
                args.checkpoint_id
                or f"{timestamp_slug()}-{args.event}-{updated['current_stage_id']}",
                checkpoint_reason,
            )
        snapshot_path = None
        if args.write_snapshot:
            snapshot_reason = args.snapshot_reason or args.event
            snapshot_path = write_snapshot(
                updated,
                args.snapshot_id or f"{timestamp_slug()}-{args.event}-{updated['current_stage_id']}",
                snapshot_reason,
            )
        persist_runtime_state(updated)
        return export_state(
            updated,
            checkpoint_path=checkpoint_path,
            snapshot_path=snapshot_path,
        )


def resume_runtime(args: argparse.Namespace) -> dict[str, Any]:
    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)
        snapshot_path = Path(args.snapshot).resolve() if args.snapshot else None
        if snapshot_path is None and args.prefer_snapshot:
            snapshot_path = latest_snapshot_path(state["snapshots_dir"])

        checkpoint_path = None
        if args.checkpoint:
            checkpoint_path = Path(args.checkpoint).resolve()
        elif isinstance(state.get("resume_point"), str) and state["resume_point"] not in ("", "none"):
            resume_path = Path(state["resume_point"])
            if resume_path.exists():
                checkpoint_path = resume_path.resolve()
        if checkpoint_path is None and snapshot_path is None:
            checkpoint_path = latest_checkpoint_path(state["checkpoints_dir"])

        resumed = state
        if snapshot_path is not None:
            resumed = apply_runtime_snapshot(args.run_root, read_aclx(snapshot_path))
        elif checkpoint_path is not None:
            resumed = apply_checkpoint_delta(state, read_aclx(checkpoint_path))
        if args.apply:
            persist_runtime_state(resumed)
        return export_state(
            resumed,
            checkpoint_path=checkpoint_path,
            snapshot_path=snapshot_path,
        )


def status_runtime(args: argparse.Namespace) -> dict[str, Any]:
    with runtime_lock(args.run_root):
        return export_state(load_runtime_state(args.run_root))


def migrate_runtime(args: argparse.Namespace) -> dict[str, Any]:
    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)
        migrated = {
            "package": False,
            "checkpoints": 0,
            "snapshots": 0,
        }

        package_entries = read_aclx(state["package_path"])
        _, changed = migrate_artifact_version(package_entries)
        migrated["package"] = changed

        for checkpoint in sorted(state["checkpoints_dir"].glob("*.aclx")):
            entries = read_aclx(checkpoint)
            _, checkpoint_changed = migrate_artifact_version(entries)
            if checkpoint_changed:
                migrated["checkpoints"] += 1

        for snapshot in sorted(state["snapshots_dir"].glob("*.aclx")):
            entries = read_aclx(snapshot)
            _, snapshot_changed = migrate_artifact_version(entries)
            if snapshot_changed:
                migrated["snapshots"] += 1

        if args.apply and migrated["package"]:
            persist_runtime_state(state)

        payload = export_state(state)
        payload["migration"] = {
            "currentProtocolVersion": state["protocol_version"],
            "packageMigrated": migrated["package"],
            "checkpointsMigrated": migrated["checkpoints"],
            "snapshotsMigrated": migrated["snapshots"],
        }
        return payload


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "bootstrap":
        payload = bootstrap_runtime(args)
    elif args.command == "event":
        payload = apply_event(args)
    elif args.command == "resume":
        payload = resume_runtime(args)
    elif args.command == "status":
        payload = status_runtime(args)
    elif args.command == "migrate":
        payload = migrate_runtime(args)
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
