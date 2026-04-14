# 依赖说明与技术原理

[English](DEPENDENCIES.md) | 简体中文

这个文件是主 README 的技术补充。

如果你第一次接触这套 bundle，建议先读 [README.zh-CN.md](README.zh-CN.md)。这里更适合想继续了解依赖关系和内部设计思路的读者。

## 随包携带的技能依赖

### `phase-stage-autoplan-entry`

- 直接依赖 `phase-stage-autorun-protocol`
- 负责生成后续执行层要使用的规划工件
- 普通规划阶段不依赖严格验证循环

### `phase-stage-autorun-protocol`

- 在长任务或需要机器维护进度时，依赖 `aclx-runtime` 和 `acl-x-protocol`
- 当某个 stage 进入反复审查与修复回合时，可以升级到 `generator-critic-verification-loop`
- 当真实委派开始时，会用 `codex-subagent-router` 选择子代理

### `generator-critic-verification-loop`

- 当循环变成真实的长运行共享状态流程时，依赖 `aclx-runtime`
- 用 `codex-subagent-router` 选择 generator、critic、refiner
- 在需要可恢复的共享 packet 或状态时，会结合 `acl-x-protocol`

## 外部环境依赖

这个 bundle 不会自带目标项目本身的工具链。目标机器仍然需要：

- Python 3.10+
- 可写的 Codex skills 目录
- 可写的目标项目目录
- 目标项目需要的构建/测试工具，例如 `npm`、`pytest`、`cargo`、`go`、`dotnet`

## 为什么这些辅助技能要一起打包

从表面上看，主流程很简单，但长任务在底层需要额外支撑：

- 规划需要可靠地交接给执行层
- 执行层需要在长流程里稳定记住当前进度
- 高难度 stage 需要更安全的审查与修复循环
- 真实多代理执行需要一致的路由策略

把这些辅助技能一起打包，可以避免一种很常见的失败方式：规划看起来能用，但执行到后面才发现缺少运行时或路由能力，结果流程中断。

## 技术原理

### 为什么要把规划层和执行层分开

这套 bundle 故意把两类东西分开：

- 规划工件，主要用于人类审阅和理解任务
- 执行工件，主要用于让运行中的任务保持稳定

这样既能保持计划可读，又能让执行过程更稳。

### 为什么控制状态比人类计划更结构化

面向人的工程计划主要是为了审阅。

而内部控制面和索引面会更结构化，是为了让执行层能够：

- 知道当前 phase 是哪个
- 知道哪些 stage 已经 ready
- 在缺计划时停止而不是猜
- 在长任务中更安全地恢复

### 为什么运行模型要分层

这套 bundle 不会从一开始就把所有任务都当成重型长流程。

更准确地说：

- 规划阶段保持轻量
- 分阶段执行在需要时增加更强的状态维护
- 严格验证循环只在某个 stage 真的需要时才启用

这样简单任务不会被搞得过重，复杂任务又有足够的运行保障。
