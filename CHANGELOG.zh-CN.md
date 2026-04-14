# 变更日志

[English](CHANGELOG.md) | 简体中文

## 1.1.0 - 2026-04-14

- 将发布包从“双 skill bundle”扩展为包含 6 个技能的完整套件。
- 将 `generator-critic-verification-loop`、`aclx-runtime`、`acl-x-protocol`、`codex-subagent-router` 一并纳入 `skills/`。
- 将 planning 侧的控制面和索引面 ACLX 化，新增 `planning-state.aclx`。
- 更新 autorun 解析逻辑，优先读取 ACL-X planning state，并兼容旧版内嵌 JSON metadata。
- 新增依赖说明、贡献指南和安全说明等发布文档。
- 新增 GitHub issue 模板和 pull request 模板。
- 强化 bundle 校验脚本和 CI，校验完整技能集与必需发布文件。

## 1.0.0

- 将仓库重构为 `skills/` 下的双 skill bundle。
- 将原有 `phase-stage-autorun-protocol` 迁移到 `skills/phase-stage-autorun-protocol`。
- 新增 `phase-stage-autoplan-entry`，用于任务 intake、自适应 phase 规划、审批和 phase 扩展。
- 在 autorun runtime 中增加 phase 边界闸门，使后续 phase 仍为 `pending` 时以 `missing_plan` 和 `expand_phase_plan` 阻塞。
- 新增 bundle 级校验和两个技能的 smoke test。
