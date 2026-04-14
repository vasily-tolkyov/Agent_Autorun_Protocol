# Installation

English | [简体中文](INSTALL.zh-CN.md)

## What Gets Installed

Copy every bundled skill under `skills/` into your Codex global skills directory:

- `phase-stage-autoplan-entry`
- `phase-stage-autorun-protocol`
- `generator-critic-verification-loop`
- `aclx-runtime`
- `acl-x-protocol`
- `codex-subagent-router`

## Prerequisites

- Python 3.10 or newer
- A writable Codex skills directory
- A writable target project directory
- Whatever build/test toolchain the target project requires

## Recommended Target Layout

```text
C:\Users\86139\.codex\skills\
  phase-stage-autoplan-entry\
  phase-stage-autorun-protocol\
  generator-critic-verification-loop\
  aclx-runtime\
  acl-x-protocol\
  codex-subagent-router\
```

If your Codex home differs, replace the base path accordingly.

## Manual Install

1. Clone or download this repository.
2. Copy the contents of `skills/` into your Codex `skills` directory.
3. Confirm that each installed skill still contains `SKILL.md` and `agents/openai.yaml`.
4. Validate the bundle:

```powershell
python scripts\validate_bundle.py
```

5. Validate the installed skills:

```powershell
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\phase-stage-autoplan-entry
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\phase-stage-autorun-protocol
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\generator-critic-verification-loop
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\aclx-runtime
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\acl-x-protocol
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\codex-subagent-router
```

6. Run the bundled smoke tests:

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

## First Use

1. Use `phase-stage-autoplan-entry` to generate the plan for a target task.
2. Review the generated planning artifacts under `plans/phase-stage-autorun/<runId>/`.
3. After explicit approval, run `approve` to bootstrap `phase-stage-autorun-protocol`.
4. Let `phase-stage-autorun-protocol` execute ready stages.
5. Let `generator-critic-verification-loop` activate only when the run truly enters repeated audit/repair rounds.

## Upgrade Notes

- Preserve local modifications before overwriting an existing installation.
- Re-run validation and smoke tests after every upgrade.
- If you only copy the two top-level skills and omit the bundled dependencies, planning may work but execution will be incomplete once the run promotes to real runtime-backed delegation.
