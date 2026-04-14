# Release Checklist

English | [简体中文](RELEASE_CHECKLIST.zh-CN.md)

## Bundle Contents

- Confirm all six bundled skills exist under `skills/`.
- Confirm each skill still contains `SKILL.md` and `agents/openai.yaml`.
- Review the root docs:
  - `README*`
  - `INSTALL*`
  - `DEPENDENCIES*`
  - `CONTRIBUTING*`
  - `SECURITY*`
  - `CHANGELOG*`
  - `RELEASE_CHECKLIST*`

## Validation

- Run bundle validation:

```powershell
python scripts\validate_bundle.py
```

- Run the core smoke tests:

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

- Run Python bytecode compilation:

```powershell
python -m py_compile scripts\validate_bundle.py skills\phase-stage-autorun-protocol\scripts\autorun_protocol.py skills\phase-stage-autorun-protocol\scripts\runtime_bridge_lib.py skills\phase-stage-autorun-protocol\scripts\run_phase_stage_autorun.py skills\phase-stage-autorun-protocol\scripts\init_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\update_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\resume_from_checkpoint.py skills\phase-stage-autorun-protocol\scripts\migrate_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py skills\phase-stage-autoplan-entry\scripts\planning_lib.py skills\phase-stage-autoplan-entry\scripts\run_phase_stage_autoplan.py skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

## GitHub Packaging

- Confirm `.github/workflows/validate.yml` is present.
- Confirm issue templates and PR template are present.
- Confirm `LICENSE` and `.gitignore` are present.
- Confirm no local runtime artifacts or caches are accidentally included.

## Publication

- Create or update the GitHub repository.
- Commit the full release bundle.
- Tag the release version.
- Publish release notes from `CHANGELOG.md`.
- Re-test installation in a clean Codex environment after publishing.
