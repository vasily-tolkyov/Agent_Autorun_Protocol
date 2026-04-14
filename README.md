# Phase Stage Automation Bundle

English | [简体中文](README.zh-CN.md)

GitHub-ready Codex skill bundle for staged engineering delivery. This repository ships the full minimum working set needed to intake a task, generate adaptive phase/stage plans, execute the approved plan with runtime-backed ACL-X state, and escalate into a generator/critic/refiner loop when stage risk requires it.

## Included Skills

### Core skills

| Skill | Role | Advantages | How to use |
| --- | --- | --- | --- |
| `phase-stage-autoplan-entry` | Intake and planning entrypoint. Scans the target project, turns the task into phases and rolling stage plans, and waits for approval. | Keeps planning in `t0`, writes human-readable Markdown plans plus ACL-X control/index state, and prevents premature execution. | Use this first when the task does not already have a complete phase/stage plan. Run `intake`, review the generated plan, then run `approve` only after explicit user confirmation. |
| `phase-stage-autorun-protocol` | Runtime-backed staged executor. Consumes the approved controlling protocol and continuously advances through ready stages. | Maintains queue/cursor/state in ACL-X runtime artifacts, blocks safely at pending phase boundaries, and supports checkpoint/resume. | Use this after approval, or let `phase-stage-autoplan-entry approve` bootstrap it for you. It stays in `t0` at bootstrap and promotes only when real runtime facts require it. |
| `generator-critic-verification-loop` | High-risk verification and repair loop for real generator/critic/refiner delegation. | Adds a repeatable audit gate, hard stop rules, checkpointing, and packet discipline for non-trivial stages. | Use this only when real multi-agent execution starts. `phase-stage-autorun-protocol` can escalate into this pattern when a stage needs repeated audit/repair rounds. |

### Bundled dependency skills

| Skill | Why it is included |
| --- | --- |
| `aclx-runtime` | Owns machine-only runtime state once a run promotes to `t2` or `t3`. |
| `acl-x-protocol` | Provides the compact ACL-X bundle discipline for shared artifacts, checkpoints, and resumable deltas. |
| `codex-subagent-router` | Picks the concrete generator, critic, and refiner agents once real delegation starts. |

## Execution Flow

1. Use `phase-stage-autoplan-entry` to scan the target project and write planning artifacts under `plans/phase-stage-autorun/<runId>/`.
2. Review the generated plan. Planning stays in `t0` and does not auto-run.
3. After explicit approval, run `approve`. This bootstraps `phase-stage-autorun-protocol`.
4. `phase-stage-autorun-protocol` executes ready stages and blocks with `missing_plan` when the next phase is still pending.
5. If a stage needs repeated audit/repair rounds, escalate to `generator-critic-verification-loop` and keep shared loop state in ACL-X runtime artifacts.

## Repository Layout

```text
.
+-- .github/
+-- scripts/
+-- skills/
|   +-- phase-stage-autoplan-entry/
|   +-- phase-stage-autorun-protocol/
|   +-- generator-critic-verification-loop/
|   +-- aclx-runtime/
|   +-- acl-x-protocol/
|   \-- codex-subagent-router/
+-- CHANGELOG.md
+-- CONTRIBUTING.md
+-- DEPENDENCIES.md
+-- INSTALL.md
+-- LICENSE
+-- RELEASE_CHECKLIST.md
+-- SECURITY.md
```

## Quick Start

1. Copy every directory under `skills/` into your Codex global skills directory.
2. Validate the release bundle:

```powershell
python scripts\validate_bundle.py
```

3. Run the core smoke tests:

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

4. Start with:

```text
Use $phase-stage-autoplan-entry to plan the task.
```

5. After you approve the plan, continue with:

```text
Use $phase-stage-autorun-protocol to execute the approved plan.
```

## Documentation Map

- [INSTALL.md](INSTALL.md): installation, validation, and upgrade steps
- [DEPENDENCIES.md](DEPENDENCIES.md): bundled skill dependencies and environment requirements
- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow and release expectations
- [SECURITY.md](SECURITY.md): security reporting and artifact sanitization guidance
- [CHANGELOG.md](CHANGELOG.md): release history
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): publication checklist
