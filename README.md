# Agent Autorun Protocol

English | [简体中文](README.zh-CN.md)

This repository is a Codex skill bundle for turning a vague engineering task into a staged execution workflow.

If you only want the short version:

- `phase-stage-autoplan-entry` helps you understand the task and produce a usable engineering plan.
- `phase-stage-autorun-protocol` helps you execute that plan continuously instead of stopping after every small step.
- `generator-critic-verification-loop` helps you add a stricter review-and-repair loop when a stage is risky or easy to get wrong.

## Who This Is For

This bundle is for teams or individuals who want Codex to do more than one-off edits.

It is useful when you want Codex to:

- break a messy request into clear phases and stages
- keep working through a staged plan without losing track
- stop safely when the next phase is not fully planned yet
- apply a stronger verification loop to hard stages

You do not need to know ACL-X or the hybrid runtime model to use the bundle.

## The Three Main Skills

### `phase-stage-autoplan-entry`

What it does:
- reads the task and scans the target project
- writes a practical phase/stage engineering plan
- pauses for approval before execution starts

Why it is useful:
- gives you a concrete plan instead of jumping straight into implementation
- keeps future work visible without pretending every later detail is already known
- makes it easier to review the direction before any code is changed

How to use it:
- use this first when the task does not already have a complete phase/stage plan
- generate the plan
- review it
- approve it when you are comfortable with the breakdown

### `phase-stage-autorun-protocol`

What it does:
- takes the approved plan and executes it stage by stage
- keeps going through the current ready work instead of stopping after each stage
- blocks safely when the next phase still needs more detailed planning

Why it is useful:
- reduces drift during longer tasks
- keeps execution aligned to an explicit plan
- makes stage progression and blocking conditions easier to understand

How to use it:
- use this after `phase-stage-autoplan-entry` has produced and approved a plan
- let it continue through the current ready stages
- if it stops because the next phase is still only outlined, expand that phase and continue

### `generator-critic-verification-loop`

What it does:
- adds a three-role execution loop for difficult stages
- separates implementation, audit, and repair planning
- repeats until the work is consistently passing review

Why it is useful:
- catches mistakes that a single pass can miss
- keeps review separate from implementation
- helps hard or high-risk stages converge more reliably

How to use it:
- use this only when a stage is complex enough to need repeated review-and-repair rounds
- most normal planning and staged execution should start without it
- bring it in when simple stage execution is not enough

## Supporting Skills Included In The Bundle

These supporting skills are included so the main workflow works end-to-end:

- `aclx-runtime`
- `acl-x-protocol`
- `codex-subagent-router`

Most users do not need to start with these directly. They are bundled because the staged execution flow depends on them in advanced or long-running scenarios.

## Typical Workflow

1. Use `phase-stage-autoplan-entry` to create the initial plan.
2. Review the generated phases and stages.
3. Approve the plan.
4. Use `phase-stage-autorun-protocol` to execute the approved stages.
5. If a stage turns out to be unusually risky or unstable, bring in `generator-critic-verification-loop`.

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

## How It Works Under The Hood

The bundle has a planning layer, an execution layer, and an optional strict verification layer.

- Planning turns the task into phases and stages.
- Execution walks through the ready stages continuously.
- Strict verification adds deeper review when a stage needs more than a single implementation pass.

If you want the technical details behind the shared state model, runtime behavior, and bundled dependencies, see [DEPENDENCIES.md](DEPENDENCIES.md).

## Documentation Map

- [INSTALL.md](INSTALL.md): installation, validation, and upgrade steps
- [DEPENDENCIES.md](DEPENDENCIES.md): dependencies and technical design notes
- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow and release expectations
- [SECURITY.md](SECURITY.md): security reporting and artifact sanitization guidance
- [CHANGELOG.md](CHANGELOG.md): release history
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): publication checklist
