# Phase Stage 自动化技能套件

[English](README.md) | 简体中文

这是一个面向 GitHub 发布的 Codex 技能套件，目标是把“任务 intake -> 自适应 phase/stage 规划 -> 基于 ACL-X 的分阶段执行 -> 高风险阶段的 generator/critic/refiner 循环”打包成一套可直接安装的最小闭环。

## 套件内包含的技能

### 三个核心技能

| 技能 | 作用 | 优势 | 使用方法 |
| --- | --- | --- | --- |
| `phase-stage-autoplan-entry` | 任务入口与规划器。读取用户任务和目标项目，生成 phase/stage 工程计划，并在批准前停住。 | 保持在 `t0`，输出 Markdown 工程计划，同时把控制面和索引面写成 ACL-X，不会边规划边误执行。 | 当任务还没有完整 phase/stage 计划时先用它。先运行 `intake`，审阅计划，只有在用户明确批准后才运行 `approve`。 |
| `phase-stage-autorun-protocol` | 分阶段执行器。读取已批准的控制协议，连续执行当前 ready 的 stage。 | 用 ACL-X runtime artifact 维护 queue/cursor/state，支持 checkpoint/resume，并且在下一个 phase 仍是 `pending` 时安全阻塞。 | 审批通过后使用，或者由 `phase-stage-autoplan-entry approve` 自动 bootstrap。它会在 bootstrap 阶段停留在 `t0`，只有运行事实满足时才升级。 |
| `generator-critic-verification-loop` | 高风险阶段的三代理执行/审计/修复循环。 | 把 generator、critic、refiner 的职责严格分离，带来更稳定的审计门、硬 stop rule 和可恢复 loop。 | 只有在真的开始多代理循环时才使用。通常由 `phase-stage-autorun-protocol` 在某个 stage 进入重复 audit/repair 回合后接管。 |

### 随包携带的依赖技能

| 技能 | 为什么要一起发布 |
| --- | --- |
| `aclx-runtime` | 当运行升级到 `t2/t3` 后，负责 machine-only 运行状态。 |
| `acl-x-protocol` | 负责共享 artifact、checkpoint 和可恢复 delta 的紧凑 ACL-X 表达。 |
| `codex-subagent-router` | 当真实委派开始时，用它选择 generator、critic、refiner 等子代理。 |

## 典型使用流程

1. 先用 `phase-stage-autoplan-entry` 对目标项目做 intake，并在 `plans/phase-stage-autorun/<runId>/` 下生成计划。
2. 审阅计划。规划阶段停留在 `t0`，不会自动开跑。
3. 用户明确批准后运行 `approve`，这一步会 bootstrap `phase-stage-autorun-protocol`。
4. `phase-stage-autorun-protocol` 连续执行当前 ready phase 的 stage；如果后续 phase 还没细化，就用 `missing_plan` 阻塞并等待 `expand-phase`。
5. 某个 stage 如果进入重复 audit/repair 回合，再升级到 `generator-critic-verification-loop`，并把共享 loop state 交给 ACL-X runtime artifact。

## 仓库结构

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

## 快速开始

1. 将 `skills/` 下的所有目录复制到你的 Codex 全局技能目录。
2. 运行套件校验：

```powershell
python scripts\validate_bundle.py
```

3. 运行核心 smoke test：

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

4. 在 Codex 中先这样使用：

```text
Use $phase-stage-autoplan-entry to plan the task. / 使用$phase-stage-autoplan-entry进行计划规划。
```

5. 计划批准后再这样继续：

```text
Use $phase-stage-autorun-protocol to execute the approved plan. / 使用$phase-stage-autorun-protocol执行已批准的计划。
```

## 文档导航

- [INSTALL.zh-CN.md](INSTALL.zh-CN.md)：安装、校验与升级步骤
- [DEPENDENCIES.zh-CN.md](DEPENDENCIES.zh-CN.md)：依赖技能和环境依赖说明
- [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)：贡献流程
- [SECURITY.zh-CN.md](SECURITY.zh-CN.md)：安全报告与工件脱敏要求
- [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)：版本历史
- [RELEASE_CHECKLIST.zh-CN.md](RELEASE_CHECKLIST.zh-CN.md)：发布检查清单
