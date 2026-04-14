# 贡献指南

[English](CONTRIBUTING.md) | 简体中文

## 适用范围

这个仓库是一个面向发布的 Codex 技能套件。提交改动时需要保持以下约束：

- `t0 -> t3` 的 runtime 分层边界
- 规划工件与执行 runtime 工件分离
- Markdown 工程语义与 ACL-X 控制面/索引面分离

## 推荐工作流

1. 在 `skills/` 下修改对应技能。
2. 如果 bundle 内容或行为发生变化，同步更新仓库根目录发布文档。
3. 运行 bundle 校验：

```powershell
python scripts\validate_bundle.py
```

4. 运行核心 smoke test：

```powershell
python skills\phase-stage-autorun-protocol\scripts\smoke_test_runtime_bridge.py
python skills\phase-stage-autoplan-entry\scripts\smoke_test_autoplan_entry.py
```

5. 任何用户可见行为变化，都要同步更新英文和中文根文档。

## 提交规则

- 不要把仅用于发布的文档塞进单个 skill 目录内部。
- 每个 skill 目录都必须保持“可单独复制到 Codex `skills` 目录后使用”。
- 尽量保持计划工件和 runtime artifact 契约向后兼容。
- 如果删除或替换 bundle 内的依赖 skill，必须同步更新文档、校验脚本和安装说明。
- 提交前对示例 artifact 做脱敏处理。

## Pull Request 要求

- 说明改动影响的是哪个 skill 或根文档。
- 说明变更属于规划层、执行层、runtime state，还是发布打包层。
- 在 PR 描述里附上校验结果。
