from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = ROOT / "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED_SKILLS = [
    "phase-stage-autoplan-entry",
    "phase-stage-autorun-protocol",
    "generator-critic-verification-loop",
    "aclx-runtime",
    "acl-x-protocol",
    "codex-subagent-router",
]

REQUIRED_ROOT_FILES = [
    ROOT / "README.md",
    ROOT / "README.zh-CN.md",
    ROOT / "INSTALL.md",
    ROOT / "INSTALL.zh-CN.md",
    ROOT / "DEPENDENCIES.md",
    ROOT / "DEPENDENCIES.zh-CN.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CONTRIBUTING.zh-CN.md",
    ROOT / "SECURITY.md",
    ROOT / "SECURITY.zh-CN.md",
    ROOT / "CHANGELOG.md",
    ROOT / "CHANGELOG.zh-CN.md",
    ROOT / "RELEASE_CHECKLIST.md",
    ROOT / "RELEASE_CHECKLIST.zh-CN.md",
    ROOT / "LICENSE",
    ROOT / ".gitignore",
    ROOT / ".github" / "workflows" / "validate.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
    ROOT / ".github" / "pull_request_template.md",
]


def validate_file_exists(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required bundle file: {path}")


def validate_skill(skill_root: Path) -> None:
    if not skill_root.exists():
        raise SystemExit(f"Missing skill directory: {skill_root}")

    skill_md = skill_root / "SKILL.md"
    agents_yaml = skill_root / "agents" / "openai.yaml"
    if not skill_md.exists():
        raise SystemExit(f"Missing SKILL.md: {skill_md}")
    if not agents_yaml.exists():
        raise SystemExit(f"Missing agents/openai.yaml: {agents_yaml}")

    content = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise SystemExit(f"Missing YAML frontmatter in {skill_md}")
    frontmatter = match.group(1)
    if "name:" not in frontmatter or "description:" not in frontmatter:
        raise SystemExit(f"Missing required frontmatter keys in {skill_md}")


def main() -> int:
    for path in REQUIRED_ROOT_FILES:
        validate_file_exists(path)

    for skill_name in REQUIRED_SKILLS:
        validate_skill(SKILLS_ROOT / skill_name)

    print(f"bundle validation passed for {len(REQUIRED_SKILLS)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
