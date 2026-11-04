#!/usr/bin/env python3
"""claude-home의 공통 규칙·스킬·검사 도구를 프로젝트나 사용자 설정으로 복사합니다.

기본은 미리보기입니다. 무엇을 바꿀지만 보여 주고, --apply를 붙여야 실제로 씁니다.

  프로젝트:  python -I scripts/sync_rules.py --target ../my-app [--lang python] [--translation] [--apply]
  사용자:    python -I scripts/sync_rules.py --user [--apply]
  스킬 사본: python -I scripts/sync_rules.py --mirror [--apply]

- 공통 규칙은 claude-home `AGENTS.md`의 common-rules 표시 사이 부분입니다. 대상 `AGENTS.md`에서는
  같은 표시 사이만 바꾸고, 표시가 없으면 맨 아래에 붙입니다. 표시 밖의 저장소 안내는 건드리지 않습니다.
- 스킬 원본은 `.agents/skills/`(Codex)이고, 같은 내용을 `.claude/skills/`(Claude Code)에도 둡니다.
- 공통 규칙이 AGENTS.md로 옮겨지기 전의 사본(`.claude/rules/basics.md` 등, `.claude/commands/`)은 지웁니다.

표준 라이브러리만 씁니다.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
BLOCK_START = "<!-- claude-home:common-rules:start -->"
BLOCK_END = "<!-- claude-home:common-rules:end -->"
LANGUAGES = ("java", "python", "typescript", "dart", "go")
PROJECT_SKILLS = ("update-docs",)
TRANSLATION_SKILLS = ("translate-chapter", "review-translation")
CHECK_SCRIPTS = ("repo_checks.py", "check_doc_links.py", "test_checks.py")
# 공통 규칙이 AGENTS.md 하나로 합쳐지기 전에 따로 복사하던 파일
LEGACY_RULE_FILES = ("basics.md", "coding.md", "docs.md", "git.md")
USER_RULES_FILE = "claude-home.md"
CLAUDE_IMPORT_LINE = "@AGENTS.md"


@dataclass(frozen=True)
class Change:
    path: Path
    content: bytes | None  # None이면 지움
    note: str = ""


@dataclass
class Plan:
    changes: list[Change]
    warnings: list[str]
    unchanged: int = 0


def extract_block(text: str) -> str:
    """시작·끝 표시를 포함한 공통 규칙 부분을 돌려줍니다."""
    start = text.find(BLOCK_START)
    end = text.find(BLOCK_END)
    if start < 0 or end < start:
        raise ValueError(f"공통 규칙 표시({BLOCK_START} … {BLOCK_END})를 찾지 못했습니다")
    return text[start : end + len(BLOCK_END)]


def merge_block(existing: str, block: str) -> str:
    """기존 문서의 공통 규칙 부분만 바꿉니다. 표시가 없으면 맨 아래에 붙입니다."""
    start = existing.find(BLOCK_START)
    end = existing.find(BLOCK_END)
    if start >= 0 and end > start:
        return existing[:start] + block + existing[end + len(BLOCK_END) :]
    body = existing.rstrip("\n")
    return f"{body}\n\n{block}\n" if body else f"{block}\n"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.is_file() else ""


def skill_files(source: Path, name: str) -> list[tuple[str, bytes]]:
    folder = source / ".agents" / "skills" / name
    if not folder.is_dir():
        raise ValueError(f"스킬 원본이 없습니다: {folder}")
    return [(p.relative_to(folder).as_posix(), p.read_bytes()) for p in sorted(folder.rglob("*")) if p.is_file()]


class Planner:
    """바꿀 파일을 모읍니다. 내용이 같으면 바꾸지 않습니다."""

    def __init__(self) -> None:
        self.plan = Plan(changes=[], warnings=[])

    def write(self, path: Path, content: bytes, note: str = "") -> None:
        if path.is_file() and path.read_bytes() == content:
            self.plan.unchanged += 1
            return
        self.plan.changes.append(Change(path, content, note or ("바꿈" if path.exists() else "새로 만듦")))

    def write_text(self, path: Path, text: str, note: str = "") -> None:
        self.write(path, text.encode("utf-8"), note)

    def delete(self, path: Path, note: str) -> None:
        if path.is_file():
            self.plan.changes.append(Change(path, None, note))

    def warn(self, message: str) -> None:
        self.plan.warnings.append(message)

    def copy_skill(self, source: Path, name: str, *skill_roots: Path) -> None:
        for rel, content in skill_files(source, name):
            for root in skill_roots:
                self.write(root / name / rel, content)


def plan_project(source: Path, target: Path, languages: list[str], translation: bool) -> Plan:
    block = extract_block(read_text(source / "AGENTS.md"))
    planner = Planner()

    agents = target / "AGENTS.md"
    existing = read_text(agents) or f"# {target.name}\n\n<!-- 저장소 안내(무엇인지, 명령어, 구조)를 여기에 적습니다. -->\n"
    planner.write_text(agents, merge_block(existing, block))

    claude = target / "CLAUDE.md"
    if not claude.is_file():
        planner.write_text(claude, f"{CLAUDE_IMPORT_LINE}\n")
    elif CLAUDE_IMPORT_LINE not in read_text(claude).splitlines():
        planner.warn(f"{claude}: `{CLAUDE_IMPORT_LINE}` 줄이 없어 Claude Code가 공통 규칙을 읽지 않습니다. 맨 위에 넣으세요")

    rules = target / ".claude" / "rules"
    installed = [lang for lang in LANGUAGES if (rules / "lang" / f"{lang}.md").is_file()]
    for lang in sorted(set(languages) | set(installed)):
        planner.write(rules / "lang" / f"{lang}.md", (source / ".claude/rules/lang" / f"{lang}.md").read_bytes())

    translation = translation or (rules / "translation.md").is_file()
    skills = list(PROJECT_SKILLS)
    if translation:
        planner.write(rules / "translation.md", (source / ".claude/rules/translation.md").read_bytes())
        skills += TRANSLATION_SKILLS
    for name in skills:
        planner.copy_skill(source, name, target / ".agents/skills", target / ".claude/skills")
        planner.delete(target / ".claude/commands" / f"{name}.md", "지움 (스킬로 옮겨짐)")

    for script in CHECK_SCRIPTS:
        planner.write(target / "scripts" / script, (source / "templates/ci" / script).read_bytes())

    for name in LEGACY_RULE_FILES:
        planner.delete(rules / name, "지움 (공통 규칙이 AGENTS.md로 옮겨짐)")
    return planner.plan


def plan_user(source: Path, home: Path) -> Plan:
    block = extract_block(read_text(source / "AGENTS.md"))
    claude_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
    codex_dir = Path(os.environ.get("CODEX_HOME") or home / ".codex")
    planner = Planner()

    planner.write_text(claude_dir / "rules" / USER_RULES_FILE, f"{block}\n")
    for rule in sorted((source / ".claude/rules").rglob("*.md")):
        planner.write(claude_dir / "rules" / rule.relative_to(source / ".claude/rules"), rule.read_bytes())
    planner.write_text(codex_dir / "AGENTS.md", merge_block(read_text(codex_dir / "AGENTS.md"), block))

    for folder in sorted((source / ".agents/skills").iterdir()):
        if folder.is_dir():
            planner.copy_skill(source, folder.name, home / ".agents/skills", claude_dir / "skills")
            planner.delete(claude_dir / "commands" / f"{folder.name}.md", "지움 (스킬로 옮겨짐)")

    for name in LEGACY_RULE_FILES:
        planner.delete(claude_dir / "rules" / name, f"지움 (공통 규칙이 {USER_RULES_FILE}로 옮겨짐)")
    return planner.plan


def plan_mirror(root: Path) -> Plan:
    """`.agents/skills/`(원본)를 `.claude/skills/`에 그대로 맞춥니다."""
    planner = Planner()
    source_dir = root / ".agents/skills"
    mirror_dir = root / ".claude/skills"
    names = sorted(p.name for p in source_dir.iterdir() if p.is_dir()) if source_dir.is_dir() else []
    for name in names:
        planner.copy_skill(root, name, mirror_dir)
    if mirror_dir.is_dir():
        for path in sorted(mirror_dir.rglob("*")):
            rel = path.relative_to(mirror_dir)
            if path.is_file() and not (source_dir / rel).is_file():
                planner.delete(path, "지움 (원본에 없음)")
    return planner.plan


def apply(plan: Plan) -> None:
    for change in plan.changes:
        if change.content is None:
            change.path.unlink()
            continue
        change.path.parent.mkdir(parents=True, exist_ok=True)
        change.path.write_bytes(change.content)


def report(plan: Plan, base: Path, heading: str) -> None:
    for change in plan.changes:
        try:
            shown = change.path.relative_to(base)
        except ValueError:
            shown = change.path
        print(f"  {change.note}: {shown.as_posix()}")
    for warning in plan.warnings:
        print(f"  확인 필요: {warning}")
    print(f"{heading} {len(plan.changes)}개, 같은 파일 {plan.unchanged}개, 확인 필요 {len(plan.warnings)}개")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="claude-home 규칙·스킬 동기화")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--target", help="규칙을 넣을 프로젝트 폴더")
    mode.add_argument("--user", action="store_true", help="~/.claude, ~/.codex, ~/.agents/skills에 넣기")
    mode.add_argument("--mirror", action="store_true", help="이 저장소의 .agents/skills를 .claude/skills에 맞추기")
    parser.add_argument("--lang", nargs="*", default=[], choices=LANGUAGES, help="추가할 언어 규칙 (--target)")
    parser.add_argument("--translation", action="store_true", help="번역 규칙과 번역 스킬 추가 (--target)")
    parser.add_argument("--home", help="홈 폴더 대신 쓸 폴더 (--user, 시험용)")
    parser.add_argument("--apply", action="store_true", help="실제로 씁니다. 없으면 미리보기만 합니다")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.target:
            base = Path(args.target).resolve()
            if not base.is_dir():
                raise ValueError(f"프로젝트 폴더가 없습니다: {base}")
            plan = plan_project(SOURCE_ROOT, base, args.lang, args.translation)
        elif args.user:
            base = Path(args.home).resolve() if args.home else Path.home()
            plan = plan_user(SOURCE_ROOT, base)
        else:
            base = SOURCE_ROOT
            plan = plan_mirror(SOURCE_ROOT)
    except (ValueError, OSError) as error:
        print(f"동기화 실패: {error}", file=sys.stderr)
        return 1

    if args.apply:
        apply(plan)
        report(plan, base, "반영함: 바꾼 파일")
    else:
        report(plan, base, "미리보기 (--apply를 붙이면 실제로 씁니다): 바꿀 파일")
    return 0


if __name__ == "__main__":
    sys.exit(main())
