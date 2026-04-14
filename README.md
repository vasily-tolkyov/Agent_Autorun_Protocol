# Agent Autorun Protocol

English | [简体中文](README.zh-CN.md)

This repository is a Codex skill bundle for turning a vague engineering task into a staged execution workflow.

If you only want the short version:

- `phase-stage-autoplan-entry` turns a vague task into a structured engineering plan.
- `phase-stage-autorun-protocol` keeps long and complex projects moving automatically instead of waiting for manual nudges.
- `generator-critic-verification-loop` audits every completed stage before the run advances, so automatic progress stays accurate.

## Who This Is For

This bundle is for teams or individuals who want Codex to handle long-running engineering work with as little manual steering as possible.

It is especially useful when you want:

- automatic execution for long projects and complex projects, not just one-off edits
- the run to keep moving without repeated human supervision or stage-by-stage pushing
- every finished stage to pass through `$generator-critic-verification-loop` before the next stage begins, so automatic progress stays precise
- lower token cost and less coordination overhead during repeated loops and long task advancement by using an ACL-X-based control strategy

You do not need to understand ACL-X before using the bundle. The workflow is designed so you can start from the planning and execution entrypoints first, then read the implementation notes later if you need them.

The bundle is usually more stable when it is used together with `ACLX_hybrid_Strategy`, because that pairing keeps lightweight work simple while making long-running loops, resumable execution, and automatic advancement more disciplined.

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

- it is built for long-running projects and complex engineering work
- it keeps advancing without routine human prompting or supervision
- it keeps execution aligned to an explicit plan instead of drifting mid-run
- it enforces a strict post-stage audit-and-repair gate before the next stage starts

How to use it:

- use this after `phase-stage-autoplan-entry` has produced and approved a plan
- let it continue through the current ready stages
- expect every completed stage to be audited and repaired as needed through `generator-critic-verification-loop` before the run advances
- if it stops because the next phase is still only outlined, expand that phase and continue

### `generator-critic-verification-loop`

What it does:

- adds a three-role execution loop after each completed stage in the autorun flow
- separates implementation, audit, and repair planning
- repeats until the work is consistently passing review

Why it is useful:

- catches mistakes that a single pass can miss
- keeps review separate from implementation
- helps long automatic runs stay accurate instead of only moving fast

How to use it:

- in the full autorun flow, treat this as the required post-stage audit gate
- each stage build is reviewed here before the next stage begins
- use it directly on its own only when you want the same strict review-and-repair loop outside the full staged autorun workflow

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
5. After each stage build, let `generator-critic-verification-loop` audit and repair the result before the run advances.

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

The bundle has a planning layer, an execution layer, and a strict verification layer.

- Planning turns the task into phases and stages.
- Execution walks through the ready stages continuously.
- Strict verification audits every completed stage before the next one begins.

If you want the technical details behind the shared state model, runtime behavior, and bundled dependencies, see [DEPENDENCIES.md](DEPENDENCIES.md).

## Documentation Map

- [INSTALL.md](INSTALL.md): installation, validation, and upgrade steps
- [DEPENDENCIES.md](DEPENDENCIES.md): dependencies and technical design notes
- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow and release expectations
- [SECURITY.md](SECURITY.md): security reporting and artifact sanitization guidance
- [CHANGELOG.md](CHANGELOG.md): release history
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): publication checklist
