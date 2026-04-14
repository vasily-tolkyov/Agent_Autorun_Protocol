# Dependencies

English | [简体中文](DEPENDENCIES.zh-CN.md)

## Skill Dependency Graph

```text
phase-stage-autoplan-entry
  -> phase-stage-autorun-protocol
       -> generator-critic-verification-loop
       -> aclx-runtime
       -> acl-x-protocol
       -> codex-subagent-router
```

## Bundled Skill Dependencies

### `phase-stage-autoplan-entry`

- Hard dependency: `phase-stage-autorun-protocol`
- Runtime posture: stays in `t0`
- Output contract: Markdown planning artifacts plus `planning-state.aclx`

### `phase-stage-autorun-protocol`

- Hard dependencies for real execution: `aclx-runtime`, `acl-x-protocol`
- Escalation dependency: `generator-critic-verification-loop`
- Delegation dependency: `codex-subagent-router`
- Runtime posture: starts in `t0`, promotes only from runtime facts

### `generator-critic-verification-loop`

- Hard dependencies for real delegation: `aclx-runtime`, `codex-subagent-router`
- Optional dependency by scenario: `acl-x-protocol` when reusable shared ACL-X packets are needed
- Runtime posture: `t0` for discussion, `t3` for real three-agent execution

## External Environment Dependencies

The bundle does not ship project-specific toolchains. The target machine still needs:

- Python 3.10+
- Access to a writable Codex skills directory
- Access to a writable target project directory
- Whatever the target project needs for build/test verification, such as `npm`, `pytest`, `cargo`, `go`, or `dotnet`

## Why The Bundle Ships These Dependencies

- `phase-stage-autoplan-entry` alone can plan, but cannot deliver the task end-to-end.
- `phase-stage-autorun-protocol` can execute staged plans, but once it promotes to real runtime-backed loops it needs ACL-X runtime support.
- `generator-critic-verification-loop` is the safety layer for difficult stages and depends on both routing and machine-owned loop state.

Bundling all six skills removes the most common installation failure mode: planning appears available, but execution later stalls because one of the runtime or routing skills is missing.
