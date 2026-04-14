# Changelog

English | [简体中文](CHANGELOG.zh-CN.md)

## 1.1.0 - 2026-04-14

- Expanded the release from a two-skill bundle to a full six-skill bundle.
- Added `generator-critic-verification-loop`, `aclx-runtime`, `acl-x-protocol`, and `codex-subagent-router` to `skills/`.
- ACL-X-ized the planning control/index plane with `planning-state.aclx`.
- Updated the autorun parser to prefer the ACL-X planning state and fall back to legacy embedded JSON metadata.
- Added release-level dependency, contribution, and security documentation.
- Added GitHub issue templates and a pull request template.
- Strengthened bundle validation so CI checks the full bundled skill set and required release files.

## 1.0.0

- Reworked the repository into a two-skill bundle under `skills/`.
- Moved the existing `phase-stage-autorun-protocol` skill into `skills/phase-stage-autorun-protocol`.
- Added the new `phase-stage-autoplan-entry` companion skill for task intake, adaptive phase planning, approval, and phase expansion.
- Added a phase-boundary gate to the autorun runtime so pending next phases block with `missing_plan` and `expand_phase_plan`.
- Added bundle-level validation and smoke tests for both skills.
