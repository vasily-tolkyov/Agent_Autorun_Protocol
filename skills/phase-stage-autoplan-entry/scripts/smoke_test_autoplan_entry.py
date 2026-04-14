from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

from planning_lib import load_protocol_metadata, read_json
from run_phase_stage_autoplan import AUTORUN_DRIVER_PATH
from run_phase_stage_autoplan import main as autoplan_main


def run_autoplan(args: list[str]) -> dict:
    buffer = io.StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        rc = autoplan_main(args)
    finally:
        sys.stdout = original_stdout
    if rc != 0:
        raise AssertionError(f"Autoplan driver returned non-zero exit code for args: {args}")
    return json.loads(buffer.getvalue())


def run_autorun(args: list[str]) -> dict:
    module_name = "_phase_stage_autorun_driver_smoke"
    spec = importlib.util.spec_from_file_location(module_name, AUTORUN_DRIVER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load autorun driver: {AUTORUN_DRIVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    driver_dir = str(AUTORUN_DRIVER_PATH.parent)
    if driver_dir not in sys.path:
        sys.path.insert(0, driver_dir)
    spec.loader.exec_module(module)

    buffer = io.StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        rc = module.main(args)
    finally:
        sys.stdout = original_stdout
    if rc != 0:
        raise AssertionError(f"Autorun driver returned non-zero exit code for args: {args}")
    return json.loads(buffer.getvalue())


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="phase-stage-autoplan-") as temp_dir:
        project_root = Path(temp_dir) / "project"
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "README.md").write_text("# Demo Project\n", encoding="utf-8", newline="\n")
        (project_root / "package.json").write_text(
            '{"name":"demo","scripts":{"test":"vitest","build":"vite build"}}\n',
            encoding="utf-8",
            newline="\n",
        )
        (project_root / "src").mkdir(parents=True, exist_ok=True)

        intake = run_autoplan(
            [
                "intake",
                "--project-root",
                str(project_root),
                "--run-id",
                "demo-run",
                "--title",
                "Demo Intake",
                "--task",
                "为演示项目增加自动规划入口，并与现有阶段执行协议集成，同时确保最终验证链路完整。",
            ]
        )
        planning_root = Path(intake["planningRoot"])
        protocol_path = Path(intake["protocolPath"])
        planning_state_path = Path(intake["planningStatePath"])
        assert_equal(protocol_path.exists(), True, "protocol is created")
        assert_equal(planning_state_path.exists(), True, "planning ACL-X state is created")
        assert_equal((planning_root / "task-context.json").exists(), True, "task context is created")
        metadata = load_protocol_metadata(protocol_path)
        assert_equal(
            metadata["planningStatePath"],
            str(planning_state_path.resolve()),
            "protocol metadata resolves planning-state ACL-X",
        )
        assert_equal(metadata["approvalStatus"], "pending", "intake leaves plan pending")
        assert_equal(len(metadata["phases"]) >= 3, True, "intake creates multiple phases")
        assert_equal(len(intake["currentExecutableStages"]) >= 1, True, "intake creates current phase stages")
        assert_equal(len(intake["pendingPhaseIds"]) >= 1, True, "later phases remain pending")

        status = run_autoplan(["status", "--planning-root", str(planning_root)])
        assert_equal(status["approvalStatus"], "pending", "status reports pending approval")
        assert_equal(status["runtimeBootstrapped"], False, "runtime is not bootstrapped before approval")

        approval = run_autoplan(["approve", "--planning-root", str(planning_root)])
        runtime_root = Path(approval["runtimeRoot"])
        assert_equal(approval["approvalStatus"], "approved", "approve marks planning state approved")
        assert_equal((runtime_root / "run-package.aclx").exists(), True, "approve bootstraps runtime")
        task_context = read_json(planning_root / "task-context.json")
        assert_equal(task_context["approvalStatus"], "approved", "task context persists approval")

        boundary = None
        for _ in approval["currentExecutableStages"]:
            boundary = run_autorun(["event", "--run-root", str(runtime_root), "--event", "stage-done"])
        assert boundary is not None
        assert_equal(boundary["blocker"], "missing_plan", "phase boundary blocks on pending next phase")
        assert_equal(boundary["nextAction"], "expand_phase_plan", "phase boundary requests expand phase")

        next_phase_id = intake["pendingPhaseIds"][0]
        expanded = run_autoplan(
            [
                "expand-phase",
                "--planning-root",
                str(planning_root),
                "--phase-id",
                next_phase_id,
            ]
        )
        expanded_metadata = load_protocol_metadata(protocol_path)
        expanded_phase = next(phase for phase in expanded_metadata["phases"] if phase["id"] == next_phase_id)
        assert_equal(expanded_phase["detailStatus"], "ready", "expand-phase marks target phase ready")
        assert_equal(len(expanded_phase["stageFiles"]) >= 1, True, "expand-phase creates detailed stages")
        assert_equal(next_phase_id in expanded["readyPhaseIds"], True, "expanded phase is now ready")

    print("phase-stage-autoplan smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
