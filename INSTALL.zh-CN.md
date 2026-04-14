# 安装说明

[English](INSTALL.md) | 简体中文

## 本套件会安装哪些技能

将 `skills/` 下的以下技能全部复制到 Codex 全局技能目录：

- `phase-stage-autoplan-entry`
- `phase-stage-autorun-protocol`
- `generator-critic-verification-loop`
- `aclx-runtime`
- `acl-x-protocol`
- `codex-subagent-router`

## 前置条件

- Python 3.10 或更高版本
- 可写的 Codex skills 目录
- 可写的目标项目目录
- 目标项目自身所需的构建/测试工具链

## 推荐安装结果

```text
C:\Users\86139\.codex\skills\
  phase-stage-autoplan-entry\
  phase-stage-autorun-protocol\
  generator-critic-verification-loop\
  aclx-runtime\
  acl-x-protocol\
  codex-subagent-router\
```

如果你的 Codex home 不在这个路径，请按实际环境替换基路径。

## 手动安装步骤

1. 克隆或下载本仓库。
2. 将仓库 `skills/` 下的内容复制到你的 Codex `skills` 目录。
3. 确认每个已安装技能都保留了 `SKILL.md` 和 `agents/openai.yaml`。
4. 运行套件校验：

```powershell
python scripts\validate_bundle.py
```

5. 对已安装技能逐个运行校验：

```powershell
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\phase-stage-autoplan-entry
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\phase-stage-autorun-protocol
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\generator-critic-verification-loop
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\aclx-runtime
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\acl-x-protocol
python C:\Users\86139\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86139\.codex\skills\codex-subagent-router
```

6. 运行随包 smoke test：

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

## 首次使用建议

1. 先用 `phase-stage-autoplan-entry` 为目标任务生成计划。
2. 在 `plans/phase-stage-autorun/<runId>/` 下审阅生成的 planning artifact。
3. 用户明确批准后，再运行 `approve` 去 bootstrap `phase-stage-autorun-protocol`。
4. 由 `phase-stage-autorun-protocol` 执行当前 ready 的 stage。
5. 只有当运行真的进入重复 audit/repair 回合时，才启用 `generator-critic-verification-loop`。

## 升级说明

- 覆盖安装前先保留本地自定义修改。
- 每次升级后都重新运行校验和 smoke test。
- 如果只复制两个顶层技能而遗漏依赖技能，规划阶段通常还能工作，但一旦运行升级到真实 runtime-backed delegation，执行链就会不完整。
