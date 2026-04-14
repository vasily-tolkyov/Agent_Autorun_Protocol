from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime_bridge_lib import (
    export_state,
    initialize_state,
    now_iso,
    persist_runtime_state,
    runtime_lock,
    write_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize the phase/stage autorun runtime bridge artifacts."
    )
    parser.add_argument("--run-root", required=True, help="Target runtime root directory.")
    parser.add_argument("--run-id", required=True, help="Stable runtime identifier.")
    parser.add_argument("--title", required=True, help="Human-readable run title.")
    parser.add_argument(
        "--controlling-protocol-path",
        required=True,
        help="Path to the controlling autorun protocol.",
    )
    parser.add_argument(
        "--queue-source",
        required=True,
        help="Description or path used to derive the ordered stage queue.",
    )
    parser.add_argument(
        "--stage",
        action="append",
        dest="stages",
        required=True,
        help="Stage plan path. Repeat for each stage in execution order.",
    )
    parser.add_argument(
        "--no-status",
        action="store_true",
        help="Skip writing status.json for non-JSON consumers.",
    )
    parser.add_argument(
        "--write-snapshot",
        action="store_true",
        help="Write a full snapshot after initialization.",
    )
    parser.add_argument("--snapshot-id", help="Explicit snapshot identifier.")
    parser.add_argument(
        "--snapshot-reason",
        default="bootstrap",
        help="Reason to record in the snapshot artifact.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    run_root = Path(args.run_root).resolve()
    with runtime_lock(run_root):
        state = initialize_state(
            run_root=run_root,
            run_id=args.run_id,
            run_title=args.title,
            created_at=now_iso(),
            stage_paths=args.stages,
        )
        if args.no_status:
            state["status_path"] = None

        persist_runtime_state(
            state,
            controlling_protocol_path=str(Path(args.controlling_protocol_path).resolve()),
            queue_source=args.queue_source,
            write_status=not args.no_status,
        )
        snapshot_path = None
        if args.write_snapshot:
            snapshot_path = write_snapshot(
                state,
                args.snapshot_id or f"{args.run_id}-bootstrap",
                args.snapshot_reason,
            )
        sys.stdout.write(
            json.dumps(export_state(state, snapshot_path=snapshot_path), ensure_ascii=True, indent=2)
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
