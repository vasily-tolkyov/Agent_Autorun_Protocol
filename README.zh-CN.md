# Agent Autorun Protocol

[English](README.md) | 简体中文

这是一个面向 Codex 的技能套件，用来把一个模糊的工程任务变成“先规划、再分阶段执行、必要时加强审查”的完整流程。

如果只看一句话，可以这样理解：

- `phase-stage-autoplan-entry` 负责先把任务整理成可执行计划。
- `phase-stage-autorun-protocol` 负责按照计划连续执行，而不是做一步停一步。
- `generator-critic-verification-loop` 负责在高风险阶段加上一层更严格的审查与修复循环。

## 这套东西适合谁

它适合想让 Codex 完成不止一次性小修改的人。

尤其适合下面这些场景：

- 想先把复杂任务拆成清晰的 phase 和 stage
- 想让 Codex 按计划持续推进，而不是中途频繁丢失上下文
- 想在后续 phase 还没规划完整时安全停住
- 想在难度高的阶段增加更严格的验证流程

你不需要先理解 ACL-X 或 hybrid runtime，照着主流程使用就可以。

## 三个核心技能

### `phase-stage-autoplan-entry`

它做什么：

- 读取任务描述并扫描目标项目
- 生成 phase/stage 工程计划
- 在真正开始执行前先停下来等批准

它的优势：

- 不会一上来就直接改代码，而是先给出计划
- 能把后续工作提前铺出来，但不会假装所有细节都已经确定
- 方便你先审方向，再决定是否执行

怎么用：

- 当任务还没有完整的 phase/stage 计划时，先用它
- 先生成计划
- 审阅计划
- 确认没问题后再批准执行

### `phase-stage-autorun-protocol`

它做什么：

- 读取已经批准的计划并按 stage 逐步执行
- 对当前已经准备好的工作持续推进
- 当下一阶段还缺详细计划时安全停住

它的优势：

- 更适合长任务，不容易做到一半漂移
- 执行始终围绕明确计划推进
- 阶段推进和阻塞原因更清楚

怎么用：

- 在 `phase-stage-autoplan-entry` 产出并批准计划之后使用
- 让它持续执行当前 ready 的 stage
- 如果它因为后续 phase 还没细化而停下，再补那个 phase 的计划并继续

### `generator-critic-verification-loop`

它做什么：

- 给困难阶段增加“三角色循环”
- 把实现、审查、修复规划分开
- 持续重复直到结果稳定通过检查

它的优势：

- 能发现单轮实现容易漏掉的问题
- 审查和实现职责分离，更稳
- 对高风险阶段更容易收敛出可靠结果

怎么用：

- 只有当某个 stage 足够复杂、需要反复审查和修复时再启用
- 普通规划和普通分阶段执行一开始通常不需要它
- 当简单执行模式不够稳时再引入它

## 套件里还包含哪些辅助技能

为了让主流程真正能跑通，这个发布包还带了这些辅助技能：

- `aclx-runtime`
- `acl-x-protocol`
- `codex-subagent-router`

大多数用户不需要一开始就直接使用它们。之所以打包进去，是因为长流程或高级运行场景会依赖这些底层能力。

## 典型使用流程

1. 先用 `phase-stage-autoplan-entry` 生成任务计划。
2. 审阅生成的 phases 和 stages。
3. 批准计划。
4. 用 `phase-stage-autorun-protocol` 执行已经准备好的 stages。
5. 如果某个 stage 风险很高或反复出问题，再引入 `generator-critic-verification-loop`。

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

这套技能大致可以分成三层：

- 规划层：把任务整理成 phases 和 stages
- 执行层：按已经准备好的 stages 持续推进
- 强化验证层：在困难阶段增加更严格的审查和修复循环

如果你想看共享状态、运行机制和依赖技能的技术说明，再去看 [DEPENDENCIES.zh-CN.md](DEPENDENCIES.zh-CN.md)。

## 文档导航

- [INSTALL.zh-CN.md](INSTALL.zh-CN.md)：安装、校验与升级步骤
- [DEPENDENCIES.zh-CN.md](DEPENDENCIES.zh-CN.md)：依赖说明与技术原理
- [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)：贡献流程
- [SECURITY.zh-CN.md](SECURITY.zh-CN.md)：安全报告与工件脱敏要求
- [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)：版本历史
- [RELEASE_CHECKLIST.zh-CN.md](RELEASE_CHECKLIST.zh-CN.md)：发布检查清单
