---
name: phase-stage-autoplan-entry
description: "Collect task context from the user request plus the target project, generate adaptive phase/stage Markdown engineering plans plus ACL-X control/index artifacts under the target project, stop in pending approval state, and then hand off approved plans to phase-stage-autorun-protocol."
---

# Phase Stage Autoplan Entry

Use this skill when a task does not already have a complete phase/stage plan and Codex must first create one before staged execution can begin.

Keep this skill in `t0`.

- do not load `aclx-runtime` or `acl-x-protocol`
- do not start execution loops while planning
- do not auto-run the generated plan without explicit user confirmation

Use this skill together with [$phase-stage-autorun-protocol](/Users/86139/.codex/skills/phase-stage-autorun-protocol/SKILL.md), not as a replacement for it.

## Required workflow

Use `scripts/run_phase_stage_autoplan.py` as the primary interface:

- `intake`: create planning artifacts from the task plus project scan
- `status`: inspect current planning and approval state
- `approve`: validate the generated plan after explicit user confirmation and bootstrap the sibling autorun runtime
- `expand-phase`: generate detailed stage files for the next pending phase or a requested phase

Read [references/planning-contract.md](references/planning-contract.md) when you need the exact planning artifact contract.

## Planning rules

- write planning artifacts under `<project-root>/plans/phase-stage-autorun/<runId>/`
- keep `planning-state.aclx` as the authoritative control/index artifact for phases and current executable stage queue
- keep runtime artifacts separate under the sibling autorun runtime root
- generate all phases upfront
- leave future phases in `detailStatus: pending` until they are expanded
- detailed stages must be executable and verifiable one at a time
- do not pretend future phase detail is known when it is not; keep it pending instead

## Approval and handoff

- explicit user confirmation in the Codex conversation is the approval signal
- do not auto-run on file creation alone
- only after confirmation should you run `approve`
- `approve` must bootstrap the sibling `phase-stage-autorun-protocol` runtime using the generated `autorun-protocol.md`
