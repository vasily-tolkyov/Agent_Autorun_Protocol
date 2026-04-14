---
name: generator-critic-verification-loop
description: Dual-mode three-agent execution, verification, and repair-planning loop for non-trivial code changes, debugging, architecture work, prompt design, or other high-risk tasks where one pass is likely to miss defects. Use when Codex is already starting, or is about to start, real generator, critic, and refiner handoffs that need structured packets, checkpoints, resume/replay semantics, or machine-owned stop rules. Do not use this skill for pure discussion, design-only exploration, or tasks that only write, port, audit, benchmark, configure, or document ACL-X skills, protocols, routers, or runtime wiring; keep those runs in `t0`.
---

# Generator Critic Refiner Loop

Use this skill in two modes:

- `t0` natural-language framing mode for discussion, design, and lightweight verification with no real multi-agent handoff
- `t3` runtime mode for real generator, critic, and refiner delegation with shared machine state managed by [$aclx-runtime](/Users/86139/.codex/skills/aclx-runtime/SKILL.md)

Keep the skill in `t0` when the task is still exploratory. The moment you start real generator, critic, and refiner handoffs with shared loop state, promote the run to `t3` and let runtime artifacts become the only source of truth.

## Core idea

Run a three-agent loop with hard role separation:

1. The generator executes the current approved plan.
2. The critic audits the latest generator result against the acceptance rubric.
3. If the critic returns `FAIL`, the main agent reviews the findings and forwards only the necessary evidence to the refiner.
4. The refiner returns a complete modification plan.
5. The main agent promotes that plan into the next execution plan and sends it back to the generator.
6. Repeat until the work reaches 5 consecutive `PASS` verdicts or 10 consecutive `FAIL` verdicts.

The main agent owns routing, state transitions, checkpointing, and final judgment. The subagents do not negotiate directly with each other. Every handoff flows through the main agent.

## Mode switch

- Stay in `t0` when you are only discussing the loop, drafting acceptance criteria, or pressure-testing the approach without real subagent execution.
- Stay in `t0` when the task only writes, ports, audits, benchmarks, configures, or documents ACL-X skills, protocols, routers, or runtime wiring, even if the content mentions loops, checkpoints, or contracts.
- Promote to `t3` as soon as you open real generator, critic, and refiner threads that need persistent shared state, resumable checkpoints, or replayable handoffs.
- In `t3`, stop maintaining loop state in free text. The runtime contract becomes authoritative for state, packets, phase transitions, and stop rules.

## Agent roles

- Main agent:
  - define the acceptance rubric, stop conditions, and file-sharing boundaries
  - choose the three subagents
  - when real delegation starts, use [$codex-subagent-router](/Users/86139/.codex/skills/codex-subagent-router/SKILL.md) to choose the generator, critic, and refiner
  - upgrade the run to `t3` and hand state ownership to [$aclx-runtime](/Users/86139/.codex/skills/aclx-runtime/SKILL.md)
  - send each subagent only its role packet and the project files needed for that role
  - review critic findings before they can influence the next step
  - reject incomplete refiner plans before they can go back to the generator
  - write checkpoints after every phase transition
  - decide accept, fail, or escalate
- Generator:
  - execute the current approved plan
  - request missing files or constraints instead of guessing
  - return a `generator_run` artifact with the concrete implementation result, changed files, verification evidence, and remaining risks
  - never self-approve and never negotiate directly with the critic or refiner
- Critic:
  - verify only
  - return a `critic_audit` artifact with a verdict of `PASS` or `FAIL`
  - explain why each finding matters with file references, test evidence, or reasoning evidence
  - must not patch the work or design the fix
- Refiner:
  - consume the reviewed critic findings plus the current candidate
  - return a `refiner_plan` artifact for the next generator round
  - specify target files, intended edits, verification steps, blockers, and failure diagnosis
  - must not implement the fix and must not re-audit the work

## Routing

- Prefer one generator, one critic, and one refiner by default.
- For code tasks, use the best stack specialist as generator, `reviewer` as critic, and `refactoring-specialist`, `debugger`, or another repair-planning specialist as refiner.
- For AI, prompt, or reasoning tasks, use `ai-engineer`, `llm-architect`, `prompt-engineer`, or another best-fit specialist as generator; use `reviewer` or another independent reasoning-heavy agent as critic; use a planning-oriented specialist as refiner.
- Add more critics only for exceptional risk. Extra critics raise cost quickly and do not replace the refiner.

## Runtime entry

Once you enter real three-thread execution, use the runtime contract and packet schema in these references:

- [references/runtime-contract.md](references/runtime-contract.md)
- [references/runtime-packets.md](references/runtime-packets.md)

Treat those files as the machine contract for:

- loop state
- per-role artifacts
- allowed phases
- stop rules
- checkpoint, resume, and replay behavior

In runtime mode, the main agent is the only writer of loop state. The subagents only consume packets and emit artifacts.

## Per-thread task packets

Send role-specific context instead of broadcasting the whole repository or the whole conversation.

- Generator packet:
  - `goal`
  - `constraints`
  - `acceptance_checks`
  - `execution_plan_ref`
  - `project_files`
  - `relevant_logs`
  - `round`
  - `reply_contract = generator_run`
- Critic packet:
  - `goal`
  - `constraints`
  - `acceptance_checks`
  - `candidate_ref`
  - `changed_files`
  - `project_files`
  - `verification_commands_or_evidence`
  - `round`
  - `reply_contract = critic_audit`
- Refiner packet:
  - `goal`
  - `constraints`
  - `acceptance_checks`
  - `candidate_ref`
  - `reviewed_findings_ref`
  - `project_files`
  - `repeated_issue_history`
  - `round`
  - `reply_contract = refiner_plan`

## Runtime state

In `t3`, use structured artifacts instead of free-text state:

- `loop_state`
- `generator_run`
- `critic_audit`
- `refiner_plan`
- `event_log`

The exact required fields live in [references/runtime-contract.md](references/runtime-contract.md). Do not rename the core phase values or artifact names.

## Working loop

### 1. Frame the task

- In `t0`, restate the goal, hard constraints, and acceptance criteria in natural language.
- Before the first real handoff, initialize runtime state and switch the run to `t3`.
- Set the gate exactly as:
  - accept after 5 consecutive `PASS` verdicts
  - fail after 10 consecutive `FAIL` verdicts

### 2. Launch the three threads

- Open one generator thread, one critic thread, and one refiner thread.
- Send each thread its own role packet with only the project files it needs.
- Keep shared state in runtime artifacts, not in the subagents.

### 3. Execute

- Dispatch `generator_packet`.
- Require a `generator_run` reply artifact.
- Record the dispatch and the reply in `event_log`.

### 4. Audit

- Dispatch `critic_packet`.
- Require a `critic_audit` reply artifact with a verdict of `PASS` or `FAIL`.
- Use these finding classes:
  - `Blocking Defect`: invalidates the result or required behavior
  - `Repairable Gap`: fixable but still a failing condition
  - `Minor Note`: non-blocking clarity or hygiene issue

The critic should stop trusting dependent steps after a `Blocking Defect`, but still inspect fully independent branches.

### 5. Review the audit

- Review the critic report before forwarding anything.
- Drop duplicates, false positives, and unsupported claims.
- Keep only the necessary findings and evidence in the reviewed repair brief.
- Increment counters exactly as follows:
  - on `PASS`: `clean_pass_streak += 1`, `fail_streak = 0`
  - on `FAIL`: `clean_pass_streak = 0`, `fail_streak += 1`

### 6. Handle pass or fail

- If the critic returns `PASS`:
  - keep the current candidate as `release_candidate_id`
  - continue the loop until `clean_pass_streak == 5`
  - transition to `terminal_accept` when the fifth consecutive pass lands
- If the critic returns `FAIL`:
  - forward the reviewed repair brief and the relevant project files to the refiner
  - require a `refiner_plan` reply artifact before the generator runs again
  - reject incomplete plans and keep the phase at `validate_refiner`
  - once the plan is complete, promote it into the next `execution_plan_ref` and dispatch the generator for the next round

### 7. Stop conditions

- Accept when `clean_pass_streak` reaches 5 and set phase to `terminal_accept`.
- Fail the task when `fail_streak` reaches 10 and set phase to `terminal_fail`.
- If the same blocking issue survives 2 failed rounds, force a strategy change:
  - swap the generator
  - swap the refiner
  - expand the file packet
  - or stop and report the blocker clearly as `strategy change required`

## Refiner plan quality gate

Require every `refiner_plan` to include all of the following before handing it back to the generator:

- `failure_diagnosis`
- `target_files`
- `edit_actions`
- `verification_steps`
- `blockers`

If any field is missing, set `plan_complete = false`, keep the phase at `validate_refiner`, and do not send the plan back to the generator.

## Checkpoint, resume, replay

- Write a checkpoint after every phase transition.
- Each checkpoint must include at least `loop_state`, the latest event, and the latest artifact references.
- On resume, restore from `phase` and `current_round` exactly. Do not guess the current round from conversation history.
- If the interruption happened during an `await_*` phase, read the latest successful dispatch packet and the latest full checkpoint before deciding whether to re-dispatch.
- Use `event_log` as the replay source. Do not reconstruct machine state from free-text dialogue.
- After resume, reconcile the latest artifacts with `loop_state`. If anything is out of sync, move into `review_critic` or `validate_refiner` before dispatching the generator again.

## Token hygiene

- Never send the entire conversation history to all three subagents each round.
- Send only the current task framing, the reviewed issue list, the role packet, and the minimal project files needed for that role.
- Resend only the files that changed or became newly relevant.
- Keep critic findings terse and quote only the minimum needed for anchoring.
- Reuse stable role prompts; avoid prompt drift.

## References

- Read [references/runtime-contract.md](references/runtime-contract.md) for the ACL-X machine contract, core artifacts, invariants, and phase transitions.
- Read [references/runtime-packets.md](references/runtime-packets.md) for the stable generator, critic, and refiner packet schemas.
- Read [references/prompt-templates.md](references/prompt-templates.md) when you need ready-to-use generator, critic, refiner, dispatch, checkpoint review, and resume reconciliation prompts.
- Read [references/ucla-method-notes.md](references/ucla-method-notes.md) for the extracted method details from the UCLA paper.
- Read [references/cost-model.md](references/cost-model.md) when the user asks for token overhead, stopping thresholds, or expected quality lift for the three-agent loop.
