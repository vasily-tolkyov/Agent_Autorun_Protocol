# Phase/Stage Autorun Runtime Versioning

Current stable protocol version: `phase-stage-autorun/codex-v1`

## Rules

- Treat `run-package.aclx` as the authoritative schema carrier.
- Require every checkpoint and snapshot artifact to include the same `protocolVersion`.
- Refuse unknown versions by default.
- Use `scripts/migrate_runtime_bridge.py` or `scripts/run_phase_stage_autorun.py migrate` to validate runtime artifacts after upgrades.

## Current release policy

- `v1` is the first stable release schema.
- Migration for `v1 -> v1` is validation-only.
- Future versions must either:
  - provide an explicit artifact rewrite path, or
  - declare the older version unsupported and fail fast before execution continues.

## Compatibility expectations

- `status.json` is a compatibility mirror and may evolve independently from ACL-X artifact details, but must never become authoritative.
- Snapshot and checkpoint artifacts must remain resumable into the current `run-package.aclx` semantics.
- If a later version changes field names or state transitions, add the migration logic to `runtime_bridge_lib.py` before publishing that version.
