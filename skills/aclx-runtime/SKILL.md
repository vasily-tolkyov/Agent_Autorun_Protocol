---
name: aclx-runtime
description: Use only after the current run has started reusable machine-only ACL-X state.
---

# ACL-X Runtime
Use this skill only after reusable machine-only state is already live.
Meta discussion is not enough.
- Default admission is `t0`.
- `t1`: one real handoff or one shared package.
- `t2`: 2+ handoffs/agents or reusable state across steps.
- `t3`: loop, repeated resume, checkpoint/replay, or repeated rounds.
- Do not promote from ACL-X wording alone.
- If the task only writes or ports a skill/protocol/router/doc, stay in `t0`.
