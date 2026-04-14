from __future__ import annotations

import json
import tempfile
from pathlib import Path

from autorun_protocol import load_protocol_metadata
from run_phase_stage_autorun import main as driver_main


def run_driver(args: list[str]) -> dict:
    import io
    import sys

    buffer = io.StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        rc = driver_main(args)
    finally:
        sys.stdout = original_stdout
    if rc != 0:
        raise AssertionError(f"Driver returned non-zero exit code for args: {args}")
    return json.loads(buffer.getvalue())


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="phase-stage-autorun-") as temp_dir:
        root = Path(temp_dir)
        plans = root / "plans"
        run_root = root / "runtime"
        plans.mkdir(parents=True, exist_ok=True)

        protocol_path = plans / "autorun.md"
        stage_one = plans / "stage-01.md"
        stage_two = plans / "stage-02.md"

        protocol_path.write_text(
            "# autorun\n\n1. stage-01.md\n2. stage-02.md\n",
            encoding="utf-8",
            newline="\n",
        )
        stage_one.write_text("# stage 01\n", encoding="utf-8", newline="\n")
        stage_two.write_text("# stage 02\n", encoding="utf-8", newline="\n")

        boot = run_driver(
            [
                "bootstrap",
                "--run-root",
                str(run_root),
                "--run-id",
                "demo-run",
                "--title",
                "Demo Autorun",
                "--controlling-protocol-path",
                str(protocol_path),
            ]
        )
        assert_equal(boot["currentStageId"], "stage-01", "bootstrap current stage")
        assert_equal(boot["stageState"], "planned", "bootstrap stage state")

        run_driver(["event", "--run-root", str(run_root), "--event", "implementation-started"])
        build_verified = run_driver(
            [
                "event",
                "--run-root",
                str(run_root),
                "--event",
                "build-verified",
                "--latest-verification",
                "build-ok",
                "--write-checkpoint",
                "--checkpoint-reason",
                "post-build-verify",
            ]
        )
        assert_equal(build_verified["stageState"], "build_verified", "build verified state")
        checkpoint_after_build = build_verified["checkpointPath"]
        snapshot_after_build = run_driver(
            [
                "event",
                "--run-root",
                str(run_root),
                "--event",
                "build-verified",
                "--latest-verification",
                "build-ok",
                "--write-snapshot",
                "--snapshot-reason",
                "post-build-snapshot",
            ]
        )["snapshotPath"]

        run_driver(["event", "--run-root", str(run_root), "--event", "protocol-reread-1"])
        run_driver(["event", "--run-root", str(run_root), "--event", "audit-started"])
        critic_fail = run_driver(
            [
                "event",
                "--run-root",
                str(run_root),
                "--event",
                "critic-fail",
                "--latest-verification",
                "critic-found-gap",
                "--write-checkpoint",
                "--checkpoint-reason",
                "critic-fail",
            ]
        )
        assert_equal(critic_fail["stageState"], "repairing", "critic fail moves to repairing")
        assert_equal(critic_fail["auditFailStreak"], 1, "critic fail increments fail streak")

        resumed = run_driver(["resume", "--run-root", str(run_root), "--checkpoint", checkpoint_after_build])
        assert_equal(resumed["stageState"], "build_verified", "resume loads explicit checkpoint")
        assert_equal(resumed["nextAction"], "protocol_reread_1", "resume next action")
        resumed_from_snapshot = run_driver(
            [
                "resume",
                "--run-root",
                str(run_root),
                "--snapshot",
                snapshot_after_build,
            ]
        )
        assert_equal(
            resumed_from_snapshot["stageState"],
            "build_verified",
            "resume loads explicit snapshot",
        )

        run_driver(["resume", "--run-root", str(run_root), "--apply"])
        run_driver(["event", "--run-root", str(run_root), "--event", "protocol-reread-1"])
        run_driver(["event", "--run-root", str(run_root), "--event", "audit-started"])
        run_driver(["event", "--run-root", str(run_root), "--event", "repair-started"])

        for _ in range(4):
            audit_progress = run_driver(
                [
                    "event",
                    "--run-root",
                    str(run_root),
                    "--event",
                    "critic-pass",
                    "--latest-verification",
                    "pass",
                ]
            )
            assert_equal(audit_progress["stageState"], "audit_running", "intermediate pass keeps audit running")

        final_pass = run_driver(
            [
                "event",
                "--run-root",
                str(run_root),
                "--event",
                "critic-pass",
                "--latest-verification",
                "pass-5",
            ]
        )
        assert_equal(final_pass["stageState"], "post_repair_verified", "fifth pass closes audit loop")
        run_driver(["event", "--run-root", str(run_root), "--event", "protocol-reread-2"])
        stage_advanced = run_driver(["event", "--run-root", str(run_root), "--event", "stage-done"])
        assert_equal(stage_advanced["currentStageId"], "stage-02", "stage done advances queue")
        assert_equal(stage_advanced["stageState"], "planned", "next stage resets to planned")

        blocked = run_driver(
            [
                "event",
                "--run-root",
                str(run_root),
                "--event",
                "blocker",
                "--blocker",
                "missing_tool",
                "--write-checkpoint",
            ]
        )
        assert_equal(blocked["blocker"], "missing_tool", "blocker records blocker enum")
        assert_equal(blocked["stageState"], "blocked", "blocker event blocks stage")

        migration = run_driver(["migrate", "--run-root", str(run_root)])
        assert_equal(
            migration["migration"]["currentProtocolVersion"],
            "phase-stage-autorun/codex-v1",
            "migration reports current version",
        )

        protocol_with_pending = plans / "autorun-pending.md"
        phase_one_dir = plans / "phase-01-foundation"
        phase_two_dir = plans / "phase-02-implementation"
        phase_one_dir.mkdir(parents=True, exist_ok=True)
        phase_two_dir.mkdir(parents=True, exist_ok=True)
        phase_one_stage = phase_one_dir / "stage-01-foundation.md"
        phase_one_stage.write_text("# stage foundation\n", encoding="utf-8", newline="\n")
        (phase_one_dir / "phase.md").write_text("# phase 1\n", encoding="utf-8", newline="\n")
        (phase_one_dir / "stage-outline.md").write_text("# outline 1\n", encoding="utf-8", newline="\n")
        (phase_two_dir / "phase.md").write_text("# phase 2\n", encoding="utf-8", newline="\n")
        (phase_two_dir / "stage-outline.md").write_text("# outline 2\n", encoding="utf-8", newline="\n")
        protocol_with_pending.write_text(
            "\n".join(
                [
                    "# autorun protocol",
                    "",
                    "```json autorun-metadata",
                    json.dumps(
                        {
                            "runId": "pending-run",
                            "approvalStatus": "approved",
                            "planningMode": "phase_upfront_stage_rolling",
                            "currentPhaseId": "phase-01-foundation",
                            "phases": [
                                {
                                    "id": "phase-01-foundation",
                                    "title": "Foundation",
                                    "path": "phase-01-foundation/phase.md",
                                    "detailStatus": "ready",
                                    "stageOutlinePath": "phase-01-foundation/stage-outline.md",
                                    "stageFiles": ["phase-01-foundation/stage-01-foundation.md"],
                                },
                                {
                                    "id": "phase-02-implementation",
                                    "title": "Implementation",
                                    "path": "phase-02-implementation/phase.md",
                                    "detailStatus": "pending",
                                    "stageOutlinePath": "phase-02-implementation/stage-outline.md",
                                    "stageFiles": [],
                                },
                            ],
                        },
                        ensure_ascii=True,
                        indent=2,
                    ),
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
        pending_metadata = load_protocol_metadata(protocol_with_pending)
        assert_equal(
            pending_metadata["phases"][1]["detailStatus"],
            "pending",
            "pending protocol metadata is readable",
        )

        boundary_run_root = root / "runtime-boundary"
        boundary_boot = run_driver(
            [
                "bootstrap",
                "--run-root",
                str(boundary_run_root),
                "--run-id",
                "pending-run",
                "--title",
                "Pending Boundary",
                "--controlling-protocol-path",
                str(protocol_with_pending),
            ]
        )
        assert_equal(
            boundary_boot["queueItems"],
            [str(phase_one_stage.resolve())],
            "bootstrap queue only includes ready phase stages",
        )
        blocked_transition = run_driver(
            ["event", "--run-root", str(boundary_run_root), "--event", "stage-done"]
        )
        assert_equal(
            blocked_transition["blocker"],
            "missing_plan",
            "phase boundary with pending next phase blocks on missing plan",
        )
        assert_equal(
            blocked_transition["nextAction"],
            "expand_phase_plan",
            "phase boundary requests phase expansion",
        )

    print("phase-stage-autorun smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
