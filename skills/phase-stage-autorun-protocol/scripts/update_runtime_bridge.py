from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from runtime_bridge_lib import (
    export_state,
    load_runtime_state,
    persist_runtime_state,
    runtime_lock,
    stage_path_for_cursor,
    timestamp_slug,
    update_stage_pointer,
    write_checkpoint,
    write_snapshot,
    derive_stage_id,
)


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "state-update"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update the phase/stage autorun runtime bridge and optionally write a checkpoint."
    )
    parser.add_argument("--run-root", required=True, help="Runtime root directory.")
    parser.add_argument("--queue-cursor", type=int, help="Updated queue cursor.")
    parser.add_argument("--current-stage-id", help="Updated stage identifier.")
    parser.add_argument("--current-stage-path", help="Updated stage file path.")
    parser.add_argument("--stage-state", help="Updated stage state.")
    parser.add_argument("--next-action", help="Updated next action.")
    parser.add_argument("--blocker", help="Updated blocker enum.")
    parser.add_argument("--audit-pass-streak", type=int, help="Updated pass streak.")
    parser.add_argument("--audit-fail-streak", type=int, help="Updated fail streak.")
    parser.add_argument("--latest-verification", help="Updated verification handle.")
    parser.add_argument("--resume-point", help="Explicit resume point override.")
    parser.add_argument(
        "--write-checkpoint",
        action="store_true",
        help="Write a checkpoint delta after applying the state update.",
    )
    parser.add_argument("--checkpoint-id", help="Explicit checkpoint identifier.")
    parser.add_argument(
        "--checkpoint-reason",
        default="state-update",
        help="Reason to record in the checkpoint delta.",
    )
    parser.add_argument(
        "--write-snapshot",
        action="store_true",
        help="Write a full snapshot after applying the state update.",
    )
    parser.add_argument("--snapshot-id", help="Explicit snapshot identifier.")
    parser.add_argument(
        "--snapshot-reason",
        default="state-update",
        help="Reason to record in the full snapshot.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)

        if args.queue_cursor is not None:
            if args.queue_cursor < 0 or args.queue_cursor >= len(state["queue_items"]):
                raise SystemExit(
                    f"--queue-cursor {args.queue_cursor} is out of range for {len(state['queue_items'])} stages"
                )
            state["queue_cursor"] = args.queue_cursor
            state["current_stage_path"] = stage_path_for_cursor(
                state["queue_items"], state["queue_cursor"]
            )
            state["current_stage_id"] = derive_stage_id(
                state["current_stage_path"], state["current_stage_id"]
            )

        if args.current_stage_path:
            state["current_stage_path"] = str(Path(args.current_stage_path).resolve())
            state["current_stage_id"] = derive_stage_id(
                state["current_stage_path"], state["current_stage_id"]
            )

        if args.current_stage_id:
            state["current_stage_id"] = args.current_stage_id

        if args.stage_state:
            state["stage_state"] = args.stage_state
        if args.next_action:
            state["next_action"] = args.next_action
        if args.blocker:
            state["blocker"] = args.blocker
        if args.audit_pass_streak is not None:
            state["audit_pass_streak"] = args.audit_pass_streak
        if args.audit_fail_streak is not None:
            state["audit_fail_streak"] = args.audit_fail_streak
        if args.latest_verification:
            state["latest_verification"] = args.latest_verification
        if args.resume_point:
            state["resume_point"] = str(Path(args.resume_point).resolve())

        if not args.current_stage_path and args.queue_cursor is None:
            update_stage_pointer(state)

        checkpoint_path = None
        if args.write_checkpoint:
            checkpoint_id = args.checkpoint_id or f"{timestamp_slug()}-{slugify(args.checkpoint_reason)}"
            checkpoint_path = write_checkpoint(state, checkpoint_id, args.checkpoint_reason)

        snapshot_path = None
        if args.write_snapshot:
            snapshot_id = args.snapshot_id or f"{timestamp_slug()}-{slugify(args.snapshot_reason)}"
            snapshot_path = write_snapshot(state, snapshot_id, args.snapshot_reason)

        persist_runtime_state(state)
        sys.stdout.write(
            json.dumps(
                export_state(state, checkpoint_path=checkpoint_path, snapshot_path=snapshot_path),
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
