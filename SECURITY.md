# Security

English | [简体中文](SECURITY.zh-CN.md)

## Reporting

If you find a security issue in this bundle, open a private security advisory or contact the maintainer through a private channel. Do not publish exploit details in a public issue first.

## What To Include

- affected skill(s)
- affected files or runtime artifacts
- reproduction steps
- expected impact
- whether secrets, tokens, or private project artifacts are involved

## Handling Runtime Artifacts

Do not publish unsanitized copies of:

- `run-package.aclx`
- `planning-state.aclx`
- checkpoint or snapshot files
- `status.json`
- target project plans if they contain sensitive paths or internal requirements

## Safe Examples

Before attaching artifacts to an issue or PR:

- remove secrets and credentials
- replace internal project names if needed
- remove private filesystem paths when they are not necessary
- avoid attaching full customer repositories or private conversation exports
