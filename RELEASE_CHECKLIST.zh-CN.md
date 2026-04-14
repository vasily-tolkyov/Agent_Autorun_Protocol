# 发布检查清单

[English](RELEASE_CHECKLIST.md) | 简体中文

## Bundle 内容检查

- 确认 `skills/` 下 6 个技能目录都存在。
- 确认每个技能都包含 `SKILL.md` 和 `agents/openai.yaml`。
- 检查根目录文档是否齐全：
  - `README*`
  - `INSTALL*`
  - `DEPENDENCIES*`
  - `CONTRIBUTING*`
  - `SECURITY*`
  - `CHANGELOG*`
  - `RELEASE_CHECKLIST*`

## 校验

- 运行 bundle 校验：

```powershell
python scripts\validate_bundle.py
```

- 运行核心 smoke test：

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

- 运行 Python 字节码编译检查：

```powershell
python -m py_compile scripts\validate_bundle.py skills\phase-stage-autorun-protocol\scripts\autorun_protocol.py skills\phase-stage-autorun-protocol\scripts\runtime_bridge_lib.py skills\phase-stage-autorun-protocol\scripts\run_phase_stage_autorun.py skills\phase-stage-autorun-protocol\scripts\init_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\update_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\resume_from_checkpoint.py skills\phase-stage-autorun-protocol\scripts\migrate_runtime_bridge.py skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py skills\phase-stage-autoplan-entry\scripts\planning_lib.py skills\phase-stage-autoplan-entry\scripts\run_phase_stage_autoplan.py skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

## GitHub 打包检查

- 确认 `.github/workflows/validate.yml` 存在。
- 确认 issue 模板和 PR 模板已补齐。
- 确认 `LICENSE` 和 `.gitignore` 存在。
- 确认没有把本地 runtime artifact 或缓存文件误提交到仓库。

## 发布

- 创建或更新 GitHub 仓库。
- 提交完整发布包。
- 打版本标签。
- 基于 `CHANGELOG.md` 发布 release notes。
- 发布后在干净的 Codex 环境里重新验证一次安装流程。
