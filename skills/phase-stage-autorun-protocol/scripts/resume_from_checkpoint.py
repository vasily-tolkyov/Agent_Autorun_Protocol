from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime_bridge_lib import (
    apply_checkpoint_delta,
    apply_runtime_snapshot,
    export_state,
    latest_checkpoint_path,
    latest_snapshot_path,
    load_runtime_state,
    persist_runtime_state,
    read_aclx,
    runtime_lock,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load the latest phase/stage autorun checkpoint and optionally apply it back to the runtime bridge."
    )
    parser.add_argument("--run-root", required=True, help="Runtime root directory.")
    parser.add_argument(
        "--checkpoint",
        help="Specific checkpoint path. Defaults to resume.point or the newest checkpoint file.",
    )
    parser.add_argument("--snapshot", help="Specific snapshot path.")
    parser.add_argument(
        "--prefer-snapshot",
        action="store_true",
        help="Prefer the newest snapshot over checkpoints when both exist.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the resumed state back into run-package.aclx, queue.md, and status.json.",
    )
    return parser


def resolve_checkpoint(args_checkpoint: str | None, state: dict[str, object]) -> Path | None:
    if args_checkpoint:
        return Path(args_checkpoint).resolve()
    resume_point = state.get("resume_point")
    if isinstance(resume_point, str) and resume_point not in ("", "none"):
        resume_path = Path(resume_point)
        if resume_path.exists():
            return resume_path.resolve()
    return latest_checkpoint_path(state["checkpoints_dir"])  # type: ignore[arg-type]


def resolve_snapshot(
    args_snapshot: str | None,
    prefer_snapshot: bool,
    state: dict[str, object],
) -> Path | None:
    if args_snapshot:
        return Path(args_snapshot).resolve()
    if prefer_snapshot:
        return latest_snapshot_path(state["snapshots_dir"])  # type: ignore[arg-type]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)
        snapshot_path = resolve_snapshot(args.snapshot, args.prefer_snapshot, state)
        checkpoint_path = resolve_checkpoint(args.checkpoint, state)
        resumed_state = state

        if snapshot_path is not None:
            resumed_state = apply_runtime_snapshot(args.run_root, read_aclx(snapshot_path))
        elif checkpoint_path is not None:
            checkpoint_entries = read_aclx(checkpoint_path)
            resumed_state = apply_checkpoint_delta(state, checkpoint_entries)
        if args.apply:
            persist_runtime_state(resumed_state)

        sys.stdout.write(
            json.dumps(
                export_state(
                    resumed_state,
                    checkpoint_path=checkpoint_path,
                    snapshot_path=snapshot_path,
                ),
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
