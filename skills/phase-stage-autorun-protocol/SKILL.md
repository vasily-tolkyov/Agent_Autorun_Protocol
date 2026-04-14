---
name: phase-stage-autorun-protocol
description: "Execute multi-phase engineering work continuously from ordered Markdown phase/stage plans, with a mandatory post-stage audit-and-repair gate on every completed stage. Start in t0, promote to t3 only when real delegation or looped repair work begins, then keep compact ACL-X control state until the final stage passes."
---

# Phase Stage Autorun Protocol

Use this skill as run policy for the entire project, not as a one-stage hint. Once execution starts, keep the same policy active until the final required stage is complete, audited, repaired, and verified, or until a hard blocker makes safe continuation impossible.

This skill is hybrid-aware:

- start in `t0`
- do not load `aclx-runtime` or `acl-x-protocol` during bootstrap
- promote to `t3` only when runtime facts require it
- after promotion, activate `$aclx-runtime` and keep the control flow in a compact ACL-X contract instead of relying on free-text memory

The goal is to preserve the current protocol's continuous execution behavior while making the outer phase/stage loop explicit enough to resist drift, pauses, and accidental early completion.

## Required inputs

Expect one of these starting points:

- an autorun protocol Markdown file that names the phase/stage sequence
- an ordered set of stage plan Markdown files
- a project root whose plan files clearly encode phase/stage order in filenames or headings

Treat the Markdown engineering plans as the authoritative scope. Do not widen scope beyond what the active stage plan or controlling autorun protocol requires.

## Runtime tiers

Use these tier boundaries exactly:

- `t0` bootstrap:
  - read the controlling protocol
  - derive the queue
  - inspect stage plans
  - initialize the run state
  - perform local preflight checks
- `t3` execution:
  - first real generator or critic or refiner handoff
  - any repeated audit and repair round
  - any checkpoint or resume requirement
  - any run that now depends on machine-managed shared state

Do not promote based on wording alone. Promote only from runtime facts. If the task only audits, ports, or edits protocol text, remain in `t0`.

When promotion occurs:

1. activate [$aclx-runtime](/Users/86139/.codex/skills/aclx-runtime/SKILL.md)
2. use [$acl-x-protocol](/Users/86139/.codex/skills/acl-x-protocol/SKILL.md) only for the reusable machine-only package, checkpoints, and resumable handoff deltas
3. stop carrying duplicated state in natural-language progress notes

## Build the execution queue

1. Read the controlling autorun protocol first when one exists.
2. If the protocol includes an explicit ordered list of stage plan files, use that list as the only execution queue.
3. Otherwise, derive the queue from the provided plan files by phase/stage order from filenames or headings.
4. Do not skip stages, reorder stages, or merge stages unless the plan files explicitly require it.
5. Keep the queue stable for the full run unless the plan documents themselves change.
6. If the controlling protocol points to `planning-state.aclx`, prefer that ACL-X control/index artifact over embedded JSON and use only the detailed stage files from phases whose `detailStatus` is `ready`.
7. If no ACL-X planning state exists but the protocol includes a machine-readable autorun metadata block, use that as the compatibility fallback.
8. When the current queue ends and the next phase is still `pending`, stop with `blocker = missing_plan` and `next_action = expand_phase_plan` instead of guessing future stage work.

## Run control state

Maintain explicit external state for the whole run. During `t0`, keep it as a concise local snapshot. After promotion to `t3`, keep the same fields in one authoritative ACL-X runtime package and update them after every child result.

Required fields:

- `queue`
- `cursor`
- `current_stage_id`
- `stage_state`
- `audit_pass_streak`
- `audit_fail_streak`
- `blocker`
- `next_action`
- `latest_verification`
- `resume_point`

Do not duplicate these fields across prose, JSON mirrors, and ACL-X unless a tool surface strictly requires a compatibility mirror. The ACL-X runtime package is authoritative after promotion.

Use this stage-state set:

- `planned`
- `implementing`
- `build_verified`
- `protocol_reread_1`
- `audit_running`
- `repairing`
- `post_repair_verified`
- `protocol_reread_2`
- `done`
- `blocked`

Use this blocker set:

- `none`
- `missing_plan`
- `missing_tool`
- `destructive_action`
- `conflicting_state`
- `unresolved_contract`

## Runtime bridge artifacts

After promotion to `t3`, create one shared task root for the autorun:

```text
.codex/phase-stage-autorun/<runId>/
  run-package.aclx
  goal.md
  status.json
  queue.md
  checkpoints/
  snapshots/
```

Use the artifacts as follows:

- `run-package.aclx`: authoritative machine-only control package
- `goal.md`: one canonical natural-language goal statement for the full autorun
- `status.json`: tiny compatibility mirror only when a tool needs JSON
- `queue.md`: stable queue inventory and stage file references
- `checkpoints/`: resumable runtime handles
- `snapshots/`: optional expanded runtime snapshots only when recovery needs more than a checkpoint delta

Keep the first user-facing task turn in natural language. After that, keep machine-only state, handoffs, checkpoints, and resumable deltas in the runtime package plus one short human gloss when needed.

Read [references/runtime-templates.md](references/runtime-templates.md) when initializing or refreshing the runtime bridge. Reuse the template pack in `templates/` instead of rewriting the artifact skeletons ad hoc.
Read [references/runtime-versioning.md](references/runtime-versioning.md) when validating installed protocol versions or preparing a release upgrade.
Use the scripts in `scripts/` as the runtime bridge interface:

- `scripts/run_phase_stage_autorun.py`: primary driver for bootstrap, event reduction, status, and resume
- `scripts/init_runtime_bridge.py`: low-level initializer for the runtime bridge artifacts
- `scripts/update_runtime_bridge.py`: low-level package updater and checkpoint writer
- `scripts/resume_from_checkpoint.py`: low-level checkpoint loader and restorer
- `scripts/migrate_runtime_bridge.py`: low-level runtime version validator and migration entrypoint
- `scripts/smoke_test_runtime_bridge.py`: project smoke test for the runtime bridge

## Compact ACL-X package

Represent the outer run in a compact ACL-X bundle, not in repeated prose. The package must encode at least:

- run identity: `runId`, title, created time
- artifact handles: `goal.md`, `queue.md`, `status.json`, `checkpoints/`, `snapshots/`
- queue state: `queue`, `cursor`, `current_stage_id`
- stage control: `stage_state`, `next_action`, `blocker`
- audit counters: `audit_pass_streak`, `audit_fail_streak`
- verification handle: `latest_verification`
- resume handle: `resume_point`
- invariants: immutable queue order, no stage skip, advance only from `done`

Keep the ACL-X terse. Prefer handles and enum-like state atoms over copied paragraphs. Do not embed full stage plans, prior chat history, or repeated acceptance prose inside the bundle.

Recommended transport pattern:

- first human request: full natural-language task
- promotion turn: one short gloss plus the shared `run-package.aclx`
- subsequent turns: handle plus compact `state_delta` only

If a child surface benefits from a readable line, use one sentence such as `Continue from the shared phase-stage runtime package.` and then reference the ACL-X artifact. Do not restate the entire stage protocol each round.

## Bootstrap and promotion gate

Run this sequence before any real delegation:

1. Read the controlling protocol and the current stage plan.
2. Build the stable execution queue.
3. Initialize the run control state with:
   - `cursor = 0`
   - `current_stage_id = queue[0]`
   - `stage_state = planned`
   - `audit_pass_streak = 0`
   - `audit_fail_streak = 0`
   - `blocker = none`
   - `next_action = read_stage_plan`
4. Perform local preflight checks for required plans, tools, permissions, and obvious repository conflicts.
5. Stay in `t0` while the work is still single-surface and local.
6. Promote to `t3` immediately when the first real generator or critic or refiner handoff starts, or when a checkpoint or repeated repair loop becomes necessary.
7. On promotion, initialize the runtime bridge:
   - create `runId`
   - prefer `scripts/run_phase_stage_autorun.py bootstrap`
   - use `scripts/init_runtime_bridge.py` only when a lower-level integration needs direct control
   - instantiate `goal.md`, `queue.md`, and authoritative `run-package.aclx` from the template pack
   - instantiate `status.json` only if a tool needs it
8. After promotion, keep control state in compact ACL-X form and do not mirror it in redundant free-text notes.

## Loop invariants

Treat these as hard rules for the full run:

- `queue` order is immutable unless the plan documents themselves change
- `cursor` advances only when `stage_state == done`
- every stage must pass through the full chain:
  - `planned -> implementing -> build_verified -> protocol_reread_1 -> audit_running -> repairing? -> post_repair_verified -> protocol_reread_2 -> done`
- no later stage work may start while the current stage is not `done`
- after every tool result or child-agent result, update the run control state before narrating progress or choosing the next step
- after every tool result or child-agent result in `t3`, prefer `scripts/run_phase_stage_autorun.py event` before any further delegation
- let the scripts hold the runtime lock and write artifacts atomically; do not hand-edit live runtime artifacts mid-run
- interrupt the user only when `blocker != none`
- the run is complete only when the final queue entry reaches `done`

## Execute each stage

For each queued stage, run this exact loop:

1. Read the current stage's Markdown plan in full and keep `stage_state = planned`.
2. Identify the stage's concrete build requirements, acceptance criteria, and dependencies on already-completed stages.
3. Implement the current stage completely enough to satisfy its plan and set `stage_state = implementing`.
4. Run the build, tests, checks, or manual verification needed to prove the stage is materially complete. On success, set `stage_state = build_verified` and `next_action = protocol_reread_1`.
5. Re-read the controlling autorun protocol immediately after the stage build and verification step. Then set `stage_state = protocol_reread_1` and `next_action = start_audit`.
6. Immediately start the stage audit-and-repair gate with `$generator-critic-verification-loop`. Set `stage_state = audit_running`.
7. Apply all valid findings from that audit to the actual stage changes. While repairs are active, set `stage_state = repairing`.
8. Re-run verification after each repair cycle. Once the repaired stage verifies cleanly under the stage gate, set `stage_state = post_repair_verified` and `next_action = protocol_reread_2`.
9. Re-read the controlling autorun protocol again after the audit-and-repair cycle finishes. Then set `stage_state = protocol_reread_2`.
10. Mark the stage `done` only when the stage is both complete and safe to continue from. Then advance `cursor`, load the next stage, and continue automatically.

## Mandatory audit-and-repair gate

After every stage build, invoke `$generator-critic-verification-loop` against the actual stage implementation, not just the written plan.

Hold the audit to these rules:

- audit the real code, configuration, tests, and artifacts changed for the stage
- fix findings rather than merely logging them
- check both functional behavior and stability
- treat regressions as stage-blocking defects
- if a repair introduces a new issue, repeat the audit-and-repair loop
- do not mark the stage done until the repaired result passes verification without unresolved critical or major issues

Use the generator-critic loop to separate implementation from adversarial checking. The stage is not finished when the first implementation lands; it is finished only after the audited and repaired version is verified.

Integrate the inner loop with the outer stage controller as follows:

- `audit_pass_streak` and `audit_fail_streak` are stage-local and reset when a new stage starts
- a critic `FAIL` never advances the stage and must keep the run on the same `current_stage_id`
- if the same blocking issue survives 2 failed rounds, force a strategy change inside the same stage before considering any escalation
- only the accepted candidate from the inner loop may move the outer stage to `post_repair_verified`

## Child-result contract

Whenever the outer run calls a child agent or a tool for stage execution, require a result shape that is easy to reduce back into run state.

At minimum, capture:

- `summary`
- `changed_files`
- `verification_evidence`
- `verdict_or_status`
- `blocker_or_none`
- `recommended_next_action`
- `state_delta`

If a child result is incomplete, derive the missing state update before doing any other work. Do not let the run continue on a purely narrative result.

For `t3` runs, child handoffs should carry:

- one short gloss line only when needed
- the shared `run-package.aclx` handle or path
- the minimal stage-specific artifact references
- the current `state_delta`

Do not resend the full protocol, full queue, or prior stage summaries to every child on every round.
Update the runtime bridge first, then delegate from the refreshed package.

## Verification standard

Before advancing, confirm all of the following:

- the current stage requirements are implemented
- prior completed stages are not regressing in functionality
- prior completed stages are not regressing in stability
- the repository remains in a state that can support the next stage
- the current stage does not depend on unverified assumptions that should have been resolved locally

If verification is weak, expand verification. Do not rely on optimistic inference when a local check is available.

## Checkpoint and resume

Once the run has promoted to `t3`, checkpoint the run control state at these minimum moments:

- after stage build verification
- after every critic verdict
- after every post-repair verification
- before any user-visible blocker report

Checkpoint rules:

- write checkpoints as compact ACL-X deltas relative to the authoritative `run-package.aclx`
- prefer `scripts/run_phase_stage_autorun.py event --write-checkpoint` for normal protocol transitions
- use `scripts/update_runtime_bridge.py --write-checkpoint` only for lower-level repair or compatibility workflows
- write full snapshots when replay safety needs more than the latest checkpoint delta
- keep `status.json` minimal and tool-facing only
- create full snapshots only when a delta would be insufficient for safe replay
- update `resume_point` after every checkpoint write

On resume:

1. prefer `scripts/run_phase_stage_autorun.py resume`
2. use `scripts/resume_from_checkpoint.py` only when a lower-level bridge integration needs the raw checkpoint or snapshot interface
3. prefer the latest explicit snapshot when the delta chain is insufficient or the caller requests snapshot recovery
4. otherwise load the latest checkpoint
5. restore `queue`, `cursor`, `current_stage_id`, `stage_state`, and `next_action` from the runtime artifacts
6. continue from `next_action` instead of re-deriving intent from conversation memory
7. do not rebuild the queue unless the plan documents changed
8. do not expand a full natural-language recap unless a human recipient explicitly needs one

## Token and time discipline

Use ACL-X to compress control state, not to restate the whole task in a new syntax.

Required efficiency rules:

- keep the initial human turn in natural language
- after promotion, treat `run-package.aclx` as the shared source of truth
- resend only `state_delta`, newly relevant file paths, and the current stage handle
- never paste full stage plans into every handoff when a file path or artifact handle is enough
- never maintain parallel long-form summaries of queue state after `t3` starts
- avoid JSON mirrors unless a tool surface cannot consume the ACL-X package directly
- prefer enum states and artifact handles over explanatory prose inside machine-only messages

## Non-interruption policy

Treat continuous execution as pre-authorized.

Do not interrupt the run for:

- routine confirmation requests
- stage-end progress reports
- plan restatements
- "ready for next stage?" questions
- requests for approval that the plan already implies
- uncertainty that can be resolved by local inspection

Interrupt only when `blocker != none`, such as:

- a required plan file is missing or unreadable
- the environment lacks a necessary tool or permission and no safe fallback exists
- the task would require a destructive or irreversible action not already authorized
- the repository or runtime is in a conflicting state that cannot be resolved locally without risking unrelated work
- the controlling contract is incomplete in a way that prevents safe execution

When a hard blocker exists, report the exact blocker, the active stage, the current `next_action`, and the smallest missing fact or permission needed to resume. Otherwise, continue without asking.

## Completion condition

Do not treat the project as complete until every required phase/stage in the execution queue has passed this full chain:

1. planned
2. built
3. audited with `$generator-critic-verification-loop`
4. repaired as needed
5. re-verified
6. reread against the controlling protocol
7. marked `done`

Completion occurs only after the final stage passes that chain. Before that point, treat the project as still in progress even if many earlier stages are already complete.

## Example invocation

```text
Use $phase-stage-autorun-protocol to execute the provided Markdown phase/stage plans continuously. Start in t0 to read the protocol, derive the queue, and preflight the current stage. Promote to t3 only when real generator or critic or refiner delegation or repeated repair work begins. Then activate $aclx-runtime, create one shared run-package.aclx, and continue by exchanging compact ACL-X state deltas for queue, cursor, stage_state, blocker, next_action, and resume_point until every stage has been built, audited, repaired, re-verified, and marked done.
```
