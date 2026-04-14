from __future__ import annotations

import argparse
import json
import sys

from runtime_bridge_lib import (
    export_state,
    load_runtime_state,
    migrate_artifact_version,
    read_aclx,
    runtime_lock,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or migrate the phase/stage autorun runtime bridge artifacts."
    )
    parser.add_argument("--run-root", required=True, help="Runtime root directory.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Reserved for future schema rewrites. Current v1 migration is validation-only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with runtime_lock(args.run_root):
        state = load_runtime_state(args.run_root)

        package_entries = read_aclx(state["package_path"])
        _, package_changed = migrate_artifact_version(package_entries)

        checkpoints_migrated = 0
        for checkpoint_path in sorted(state["checkpoints_dir"].glob("*.aclx")):
            entries, changed = migrate_artifact_version(read_aclx(checkpoint_path))
            _ = entries
            if changed:
                checkpoints_migrated += 1

        snapshots_migrated = 0
        for snapshot_path in sorted(state["snapshots_dir"].glob("*.aclx")):
            entries, changed = migrate_artifact_version(read_aclx(snapshot_path))
            _ = entries
            if changed:
                snapshots_migrated += 1

        payload = export_state(state)
        payload["migration"] = {
            "applyRequested": args.apply,
            "currentProtocolVersion": state["protocol_version"],
            "packageMigrated": package_changed,
            "checkpointsMigrated": checkpoints_migrated,
            "snapshotsMigrated": snapshots_migrated,
            "note": "Current release uses validation-only migration because v1 is the first stable schema.",
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
