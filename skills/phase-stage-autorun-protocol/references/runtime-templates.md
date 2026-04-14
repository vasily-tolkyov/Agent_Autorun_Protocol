# Phase/Stage Autorun Runtime Templates

Use this template pack only after the run has promoted from `t0` to `t3`.

The files in `templates/` are starter skeletons for the runtime bridge artifacts named in [`SKILL.md`](../SKILL.md). They standardize field names, reduce prompt drift, and keep later handoffs to handles plus compact deltas.

Use the scripts in `../scripts/` to instantiate and maintain these files:

- `run_phase_stage_autorun.py`
- `init_runtime_bridge.py`
- `update_runtime_bridge.py`
- `resume_from_checkpoint.py`
- `migrate_runtime_bridge.py`
- `smoke_test_runtime_bridge.py`

## Files

- [goal.template.md](../templates/goal.template.md): canonical natural-language goal file
- [queue.template.md](../templates/queue.template.md): stable queue inventory and cursor snapshot
- [run-package.template.aclx](../templates/run-package.template.aclx): authoritative machine-only control package skeleton
- [status.template.json](../templates/status.template.json): minimal compatibility mirror for JSON-only surfaces
- [checkpoint-delta.template.aclx](../templates/checkpoint-delta.template.aclx): resumable ACL-X delta skeleton
- [snapshot-state.template.aclx](../templates/snapshot-state.template.aclx): full-state ACL-X snapshot skeleton

## Usage rules

- Keep the first human task turn in natural language.
- Instantiate the templates once when promotion to `t3` occurs.
- Prefer `run_phase_stage_autorun.py` for normal protocol execution.
- Prefer the scripts over ad hoc manual template expansion.
- Treat `run-package.aclx` as authoritative after promotion.
- Use `status.json` only when a tool cannot consume the ACL-X package directly.
- Write checkpoints as deltas from `run-package.aclx`; use full snapshots only when replay safety requires them.
- Let the scripts hold the runtime lock and write artifacts atomically; do not hand-edit live runtime artifacts mid-run.
- Resend only a short gloss, the shared package handle, the current stage artifacts, and the latest `state_delta`.

## ACL-X template note

For this skill, the canonical emitted format is the line-based `key=value` ACL-X representation written by the scripts in `scripts/`.

Use the templates this way:

1. Preserve the field names and control semantics.
2. Let the scripts fill the placeholders from the current run state.
3. If a stricter downstream ACL-X serializer exists, translate from the same field set instead of inventing new semantics.

## Required substitutions

At minimum, replace these placeholders before runtime use:

- `{{run_id}}`
- `{{run_title}}`
- `{{created_at}}`
- `{{goal_path}}`
- `{{queue_path}}`
- `{{status_path}}`
- `{{checkpoints_dir}}`
- `{{snapshots_dir}}`
- `{{current_stage_id}}`
- `{{stage_state}}`
- `{{next_action}}`
- `{{blocker}}`
- `{{resume_point}}`

For queue and checkpoint artifacts, also replace the stage- and checkpoint-specific placeholders present in those files.

In particular:

- expand `{{ordered_stage_lines}}` into the full ordered stage list
- replace `{{queue_cursor}}` and `{{current_stage_path}}` in `queue.template.md`
- replace `{{checkpoint_id}}`, `{{run_package_path}}`, and `{{checkpoint_reason}}` in `checkpoint-delta.template.aclx`
- replace `{{snapshot_id}}`, `{{snapshot_reason}}`, `{{snapshot_created_at}}`, `{{run_created_at}}`, and `{{source_package_path}}` in `snapshot-state.template.aclx`
