# Agent Autorun Protocol

[English](README.md) | 简体中文

这是一个面向 Codex 的技能套件，用来把模糊的工程任务变成“先规划、再分阶段自动执行、并在每个阶段后强制审计”的完整工作流。

如果只看短版，可以这样理解：

- `phase-stage-autoplan-entry` 先把模糊任务整理成可执行的工程计划。
- `phase-stage-autorun-protocol` 负责自动推进长工程和复杂工程，而不是做一步停一步。
- `generator-critic-verification-loop` 会在每一个 stage 构建结束后做审计和修复规划，让自动推进保持精确。

## 这套东西适合谁

这套 bundle 适合希望让 Codex 尽量独立推进长时间、复杂工程任务的团队或个人。

它尤其适合这些场景：

- 要处理的是长工程、复杂工程、跨多个阶段的任务，而不是一次性的小修小补
- 执行过程自动持续推进，不需要人工一轮一轮催促、确认和监督
- 每一个 stage 构建结束后都经过 `$generator-critic-verification-loop` 审计，再进入下一个 stage，以保证自动推进时的准确性
- 用 ACL-X 控制策略显著降低长循环、阶段推进和恢复执行时的 token 与时间消耗

你不需要先理解 ACL-X 才能使用这套 bundle。可以先从规划入口和执行入口开始，用到时再看后面的原理说明。

和 `ACLX_hybrid_Strategy` 一起使用时，这套流程通常会更稳定，因为轻量步骤可以保持简洁，而长循环、检查点和恢复执行会更有纪律性。

## 三个核心技能

### `phase-stage-autoplan-entry`

它做什么：

- 读取任务描述并扫描目标项目
- 生成 phase/stage 工程计划
- 在真正执行前先停下来等待批准

它的优势：

- 不会一上来就直接改代码，而是先产出可审阅的计划
- 能把后续工作结构化展开，同时保留滚动细化的空间
- 让你在任何代码改动发生前先确认方向

怎么用：

- 当任务还没有完整 phase/stage 计划时，先用它
- 先生成计划
- 审阅生成结果
- 确认拆分合理后再批准执行

### `phase-stage-autorun-protocol`

它做什么：

- 读取已经批准的计划并按 stage 自动执行
- 在当前 ready 工作范围内持续推进，而不是每完成一个 stage 就停下等人推动
- 当下一个 phase 仍缺少详细计划时安全阻塞

它的优势：

- 专门面向长工程和复杂工程的自动推进
- 能在不需要日常人工监督的前提下持续前进
- 执行过程始终围绕明确计划推进，降低中途漂移
- 每个 stage 完成后都会进入严格的审计和修复门，兼顾连续性与准确性

怎么用：

- 在 `phase-stage-autoplan-entry` 生成并批准计划后使用
- 让它持续执行当前 ready 的 stages
- 预期每一个完成的 stage 都会先经过 `generator-critic-verification-loop` 审计与必要修复，再继续向前推进
- 如果它因为后续 phase 仍只有骨架而停下，就先补全那个 phase 再继续

### `generator-critic-verification-loop`

它做什么：

- 在 autorun 流程里为每一个已完成 stage 增加三角色审计循环
- 把实现、审计和修复规划分开
- 持续重复直到结果稳定通过检查

它的优势：

- 能发现单次实现容易漏掉的问题
- 把审计与实现职责分离，让结果更稳
- 让长时间自动执行不仅推进得快，也能持续保持精确

怎么用：

- 在完整 autorun 流程中，把它视为每个 stage 结束后的必经审计门
- 每一个 stage 构建结束后，都先在这里完成审计与修复判断，再进入下一个 stage
- 只有在你想单独复用同样严格的审计修复循环时，才直接单独调用它

## 套件中包含的辅助技能

为了让主流程真正端到端可运行，这个发布包还带了这些辅助技能：

- `aclx-runtime`
- `acl-x-protocol`
- `codex-subagent-router`

大多数用户不需要一开始就直接操作它们。之所以打包进来，是因为长流程、恢复执行和多代理审计场景会依赖这些底层能力。

## 典型使用流程

1. 先用 `phase-stage-autoplan-entry` 生成任务计划。
2. 审阅生成的 phases 和 stages。
3. 批准计划。
4. 用 `phase-stage-autorun-protocol` 执行已经准备好的 stages。
5. 在每一个 stage 构建结束后，让 `generator-critic-verification-loop` 先完成审计和必要修复，再进入下一个 stage。

## 快速开始

1. 把 `skills/` 下的所有目录复制到你的 Codex 全局技能目录。
2. 运行 bundle 校验：

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
Use $phase-stage-autoplan-entry to plan the task.
```

5. 计划批准后再这样继续：

```text
Use $phase-stage-autorun-protocol to execute the approved plan.
```

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

## 工作原理概览

这套 bundle 大致可以分成三层：

- 规划层：把任务整理成 phases 和 stages
- 执行层：按已经 ready 的 stages 持续推进
- 强化验证层：在每一个 stage 完成后执行严格的审计和修复循环

如果你想了解共享状态、运行机制、ACL-X 控制策略和依赖技能的技术说明，再去看 [DEPENDENCIES.zh-CN.md](DEPENDENCIES.zh-CN.md)。

## 文档导航

- [INSTALL.zh-CN.md](INSTALL.zh-CN.md)：安装、校验与升级步骤
- [DEPENDENCIES.zh-CN.md](DEPENDENCIES.zh-CN.md)：依赖说明与技术原理
- [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)：贡献流程
- [SECURITY.zh-CN.md](SECURITY.zh-CN.md)：安全报告与工件脱敏要求
- [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)：版本历史
- [RELEASE_CHECKLIST.zh-CN.md](RELEASE_CHECKLIST.zh-CN.md)：发布检查清单
