# Dependencies And Technical Notes

English | [简体中文](DEPENDENCIES.zh-CN.md)

This file is the technical companion to the main README.

If you are new to the bundle, start with [README.md](README.md) first. This file is for readers who want to understand the supporting skills and the internal design choices.

## Bundled Skill Dependencies

### `phase-stage-autoplan-entry`

- depends directly on `phase-stage-autorun-protocol`
- creates the planning artifacts used by the execution layer
- does not depend on the strict verification loop for normal planning

### `phase-stage-autorun-protocol`

- depends on `aclx-runtime` and `acl-x-protocol` for long-running or machine-managed execution
- can escalate into `generator-critic-verification-loop` when a stage needs repeated audit-and-repair rounds
- uses `codex-subagent-router` when real delegation starts

### `generator-critic-verification-loop`

- depends on `aclx-runtime` when the loop becomes a real long-running shared-state flow
- uses `codex-subagent-router` to choose generator, critic, and refiner agents
- may use `acl-x-protocol` when reusable shared packets or resumable machine state are needed

## External Environment Dependencies

The bundle does not include project-specific toolchains. The target machine still needs:

- Python 3.10+
- a writable Codex skills directory
- a writable target project directory
- the build/test tools required by the target project, such as `npm`, `pytest`, `cargo`, `go`, or `dotnet`

## Why These Supporting Skills Are Bundled

The main workflow looks simple from the outside, but long tasks need support under the hood:

- planning needs a reliable handoff into execution
- execution needs a stable way to remember progress during longer runs
- hard stages need a safer review-and-repair loop
- real multi-agent execution needs a consistent routing policy

Bundling these supporting skills avoids a common failure mode: planning works, but execution later stalls because a required runtime or routing skill is missing.

## Technical Principles

### Planning And Execution Are Separate On Purpose

The bundle separates:

- planning artifacts, which are mainly for understanding and reviewing the work
- execution artifacts, which are mainly for keeping the running task on track

This keeps planning readable while making execution more stable.

### Control State Is More Structured Than Human-Facing Plans

The visible engineering plan is written for people to review.

The internal control and index data are more structured so the execution layer can:

- know which phase is current
- know which stages are ready
- know when to stop instead of guessing
- resume long tasks more safely

### The Runtime Model Is Layered

The bundle does not treat every task as a heavy long-running workflow from the first minute.

Instead:

- planning starts lightweight
- staged execution adds stronger state handling when needed
- the strict verification loop is only used when a stage truly needs it

This keeps simple tasks simpler while still supporting difficult runs.
