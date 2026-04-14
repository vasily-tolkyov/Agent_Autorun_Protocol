from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

from planning_lib import (
    current_stage_files,
    expand_phase,
    export_planning_state,
    load_planning_state,
    mark_approved,
    now_iso,
    write_autorun_protocol,
    write_json,
    write_phase_index,
    write_planning_state,
    write_planning_bundle,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
AUTORUN_DRIVER_PATH = (
    SKILLS_ROOT / "phase-stage-autorun-protocol" / "scripts" / "run_phase_stage_autorun.py"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Intake and adaptive planning driver for phase/stage autorun tasks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    intake = subparsers.add_parser("intake", help="Collect task and project context, then write planning artifacts.")
    intake.add_argument("--project-root", required=True)
    intake.add_argument("--run-id", required=True)
    intake.add_argument("--title", required=True)
    intake.add_argument("--task", required=True)
    intake.add_argument("--planning-root")
    intake.add_argument("--success-criteria", action="append", default=[])
    intake.add_argument("--constraint", action="append", dest="constraints", default=[])

    status = subparsers.add_parser("status", help="Print current planning status.")
    status.add_argument("--planning-root", required=True)

    approve = subparsers.add_parser(
        "approve",
        help="Validate the generated plan after explicit user confirmation and bootstrap autorun runtime.",
    )
    approve.add_argument("--planning-root", required=True)
    approve.add_argument("--runtime-root")
    approve.add_argument("--no-status", action="store_true")

    expand = subparsers.add_parser("expand-phase", help="Generate detailed stage files for a pending phase.")
    expand.add_argument("--planning-root", required=True)
    expand.add_argument("--phase-id")

    return parser


def intake_task(args: argparse.Namespace) -> dict[str, Any]:
    return write_planning_bundle(
        project_root=args.project_root,
        run_id=args.run_id,
        title=args.title,
        task_text=args.task,
        success_criteria=args.success_criteria,
        constraints=args.constraints,
        planning_root=args.planning_root,
    )


def planning_status(args: argparse.Namespace) -> dict[str, Any]:
    task_context, _ = load_planning_state(args.planning_root)
    runtime_root = default_runtime_root(Path(task_context["projectRoot"]), task_context["runId"])
    payload = export_planning_state(task_context, task_context["approvalStatus"])
    payload["runtimeRoot"] = str(runtime_root)
    payload["runtimeBootstrapped"] = (runtime_root / "run-package.aclx").exists()
    payload["checkedAt"] = now_iso()
    return payload


def approve_plan(args: argparse.Namespace) -> dict[str, Any]:
    planning_root = Path(args.planning_root).resolve()
    task_context, protocol_metadata = load_planning_state(planning_root)
    current_phase_id = protocol_metadata["currentPhaseId"]
    current_phase = next(
        (phase for phase in task_context["phases"] if phase["id"] == current_phase_id),
        None,
    )
    if current_phase is None:
        raise SystemExit(f"Current phase not found: {current_phase_id}")
    if current_phase.get("detailStatus") != "ready" or not current_phase.get("stageFiles"):
        raise SystemExit(
            f"Current phase {current_phase_id} is not ready for execution. Expand the phase first."
        )

    for stage_file in current_phase["stageFiles"]:
        stage_path = planning_root / stage_file
        if not stage_path.exists():
            raise SystemExit(f"Missing stage plan required for approval: {stage_path}")

    updated_context = mark_approved(task_context)
    write_json(planning_root / "task-context.json", updated_context)
    write_phase_index(planning_root / "phase-index.md", planning_root, updated_context)
    write_planning_state(planning_root / "planning-state.aclx", planning_root, updated_context)
    write_autorun_protocol(planning_root / "autorun-protocol.md", planning_root, updated_context)

    runtime_root = (
        Path(args.runtime_root).resolve()
        if args.runtime_root
        else default_runtime_root(Path(updated_context["projectRoot"]), updated_context["runId"])
    )
    autorun_bootstrap = invoke_autorun_driver(
        [
            "bootstrap",
            "--run-root",
            str(runtime_root),
            "--run-id",
            updated_context["runId"],
            "--title",
            updated_context["title"],
            "--controlling-protocol-path",
            str((planning_root / "autorun-protocol.md").resolve()),
            *([] if not args.no_status else ["--no-status"]),
        ]
    )

    payload = export_planning_state(updated_context, updated_context["approvalStatus"])
    payload["runtimeRoot"] = str(runtime_root)
    payload["executionBootstrap"] = autorun_bootstrap
    payload["handoffSkill"] = "phase-stage-autorun-protocol"
    payload["handoffPrompt"] = (
        "Use $phase-stage-autorun-protocol with the generated autorun-protocol.md and the "
        "bootstrapped runtime package to continue execution."
    )
    return payload


def expand_phase_command(args: argparse.Namespace) -> dict[str, Any]:
    return expand_phase(planning_root=args.planning_root, phase_id=args.phase_id)


def invoke_autorun_driver(argv: list[str]) -> dict[str, Any]:
    module_name = "_phase_stage_autorun_driver"
    spec = importlib.util.spec_from_file_location(module_name, AUTORUN_DRIVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load autorun driver from {AUTORUN_DRIVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    script_dir = str(AUTORUN_DRIVER_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec.loader.exec_module(module)

    buffer = io.StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        rc = module.main(argv)
    finally:
        sys.stdout = original_stdout
    if rc != 0:
        raise RuntimeError(f"Autorun driver returned non-zero exit code for args: {argv}")
    return json.loads(buffer.getvalue())


def default_runtime_root(project_root: Path, run_id: str) -> Path:
    return project_root.resolve() / ".codex" / "phase-stage-autorun" / run_id


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "intake":
        payload = intake_task(args)
    elif args.command == "status":
        payload = planning_status(args)
    elif args.command == "approve":
        payload = approve_plan(args)
    elif args.command == "expand-phase":
        payload = expand_phase_command(args)
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
