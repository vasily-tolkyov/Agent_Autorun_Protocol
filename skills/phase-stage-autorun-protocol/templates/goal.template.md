# Goal

Title: {{run_title}}

Execute the provided phase/stage plans in strict order. Do not skip stages. Build, verify, audit, repair, re-verify, and advance only from `done`.

## Scope

- controlling_protocol: {{controlling_protocol_path}}
- queue_source: {{queue_source}}
- runtime_tier: t3

## Completion

- final_condition: every queued stage reaches `done`
- blocker_policy: interrupt only when `blocker != none`
