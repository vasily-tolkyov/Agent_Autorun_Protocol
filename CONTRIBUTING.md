# Contributing

English | [简体中文](CONTRIBUTING.zh-CN.md)

## Scope

This repository is a release bundle for a coordinated Codex skill suite. Contributions should preserve:

- the `t0 -> t3` runtime boundaries
- the separation between planning artifacts and execution runtime artifacts
- the division between Markdown engineering semantics and ACL-X control/index state

## Expected Workflow

1. Update the relevant skill under `skills/`.
2. Keep root release docs in sync when bundle contents or behavior changes.
3. Run bundle validation:

```powershell
python scripts\validate_bundle.py
```

4. Run the core smoke tests:

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

5. Update English and Chinese root docs together when user-facing behavior changes.

## Contribution Guidelines

- Do not add release-only documentation inside individual skill directories.
- Keep skills installable as standalone folders under a Codex `skills` directory.
- Prefer backward-compatible changes to plan and runtime artifact contracts.
- Do not remove bundled dependency skills without also updating docs, validation, and installation guidance.
- Sanitize any example artifacts before committing them.

## Pull Requests

- Explain which skill or root document changed.
- Describe whether the change affects planning, execution, runtime state, or release packaging.
- Include validation evidence in the PR description.
