# 依赖说明

[English](DEPENDENCIES.md) | 简体中文

## 技能依赖关系

```text
phase-stage-autoplan-entry
  -> phase-stage-autorun-protocol
       -> generator-critic-verification-loop
       -> aclx-runtime
       -> acl-x-protocol
       -> codex-subagent-router
```

## 随包携带的技能依赖

### `phase-stage-autoplan-entry`

- 硬依赖：`phase-stage-autorun-protocol`
- 运行姿态：保持在 `t0`
- 输出契约：Markdown 规划工件 + `planning-state.aclx`

### `phase-stage-autorun-protocol`

- 真实执行时的硬依赖：`aclx-runtime`、`acl-x-protocol`
- 升级到高风险循环时的依赖：`generator-critic-verification-loop`
- 真实委派时的依赖：`codex-subagent-router`
- 运行姿态：从 `t0` 启动，只根据真实运行事实升级

### `generator-critic-verification-loop`

- 真实多代理执行时的硬依赖：`aclx-runtime`、`codex-subagent-router`
- 视场景使用的依赖：当需要可复用 ACL-X packet 时可结合 `acl-x-protocol`
- 运行姿态：讨论时留在 `t0`，真正三代理执行时进入 `t3`

## 外部环境依赖

本套件不会打包目标项目自己的工具链。目标机器仍然需要：

- Python 3.10+
- 可写的 Codex skills 目录
- 可写的目标项目目录
- 目标项目本身所需的构建/测试工具，例如 `npm`、`pytest`、`cargo`、`go`、`dotnet`

## 为什么要把这些依赖一起打包

- 单独有 `phase-stage-autoplan-entry` 只能做规划，不能完整交付任务。
- `phase-stage-autorun-protocol` 能执行分阶段计划，但一旦升级到真实 runtime-backed loop，就必须有 ACL-X 运行时支撑。
- `generator-critic-verification-loop` 是高风险 stage 的安全层，本身又依赖路由和 machine-owned loop state。

把这 6 个技能一起打包，可以避免最常见的安装失败模式：看起来能规划，但运行到后面才发现缺 runtime 或 routing skill，导致执行链中断。
