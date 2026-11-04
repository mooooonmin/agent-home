#!/usr/bin/env python3
"""claude-home의 공통 규칙·스킬·검사 도구를 프로젝트나 사용자 설정으로 복사합니다.

기본은 미리보기입니다. 무엇을 바꿀지만 보여 주고, --apply를 붙여야 실제로 씁니다.

  프로젝트:  python -I scripts/sync_rules.py --target ../my-app [--lang python] [--translation] [--apply]
  사용자:    python -I scripts/sync_rules.py --user [--apply]
  스킬 사본: python -I scripts/sync_rules.py --mirror [--apply]

- 공통 규칙은 claude-home `AGENTS.md`의 common-rules 표시 사이 부분입니다. 대상 `AGENTS.md`에서는
  같은 표시 사이만 바꾸고, 표시가 둘 다 없으면 맨 아래에 붙입니다. 표시가 한쪽만 있으면 멈춥니다.
- 훅 설정(`.claude/settings.json`, `.codex/hooks.json`)은 없을 때만 템플릿으로 만듭니다. 이미 있으면 덮어쓰지 않고,
  훅(agent_hooks.py)이 빠져 있으면 알립니다.
- 스킬 원본은 `.agents/skills/`(Codex)이고, 같은 내용을 `.claude/skills/`(Claude Code)에도 둡니다.
  원본에서 없어진 스킬 파일은 사본에서도 지웁니다.
- 공통 규칙이 AGENTS.md로 옮겨지기 전의 사본(`.claude/rules/basics.md` 등, `.claude/commands/`)은
  claude-home에 있던 내용 그대로일 때만 지웁니다. 고친 흔적이 있으면 지우지 않고 알립니다.

표준 라이브러리만 씁니다.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
BLOCK_START = "<!-- claude-home:common-rules:start -->"
BLOCK_END = "<!-- claude-home:common-rules:end -->"
LANGUAGES = ("java", "python", "typescript", "dart", "go")
TRANSLATION = "translation"
# 코드·문서를 다룰 때만 읽히는 공통 규칙. 언어와 상관없이 모든 프로젝트에 넣습니다.
COMMON_RULE_FILES = ("code.md", "writing-docs.md")
PROJECT_SKILLS = ("update-docs",)
TRANSLATION_SKILLS = ("translate-chapter", "review-translation")
CHECK_SCRIPTS = ("repo_checks.py", "check_doc_links.py", "test_checks.py", "agent_hooks.py", "test_agent_hooks.py")
# 프로젝트 안의 경로 → claude-home의 템플릿. 프로젝트마다 손볼 수 있는 설정이라 없을 때만 만듭니다.
AGENT_SETTINGS = (
    (".claude/settings.json", "templates/agent-settings/claude-settings.json"),
    (".codex/hooks.json", "templates/agent-settings/codex-hooks.json"),
)
HOOK_SCRIPT_NAME = "agent_hooks.py"
USER_RULES_FILE = "claude-home.md"
CLAUDE_IMPORT_LINES = ("@AGENTS.md", "@./AGENTS.md")
# 공통 규칙이 AGENTS.md 하나로 합쳐지기 전에 따로 복사하던 파일
LEGACY_RULE_FILES = ("basics.md", "coding.md", "docs.md", "git.md")
# 위 파일과 예전 `.claude/commands/*.md`가 claude-home git 기록에 있던 모든 버전의 SHA-256(줄바꿈은 LF로 맞춤).
# 이 목록에 있는 사본만 지워서, 사용자가 고친 파일이나 이름만 같은 다른 파일을 지키기 위함입니다.
KNOWN_LEGACY_SHA256 = frozenset({
    "04033415ca79620375f5ac11677dcff547639eb4e6aeac7023aea4689bec0b47",
    "0bd3b228e9b3b6984ce025ef75e6fc95af7abdf561d0c2fe0121b65ac58e91b4",
    "13c92f070c6523bd7aa2ec89081281e80d883f6977d433a0ed4826dea6ff3a26",
    "18ca11d332a39ad15351f79becead0dd97fa017a6fe7bf2e4639da4d112d289f",
    "1a7d979bfaa2250df037b39c75e43c8b79d170e14abaf776d90aaaac6eefc6dd",
    "2b0faf20a94c8e27f76269630bc3108638ff808c5b2ade589d4af9d4bbfa44be",
    "46eda5a6250f34950e4e01dd692a860a9dc0407f86603437b4683bd08aa931fc",
    "4b03ba8b116da1f226cfe37721379f345de7451a7c0c97148d5f925a6983b889",
    "555a425db053204c121a830a08f48168dc6d6633a38c1e1ecb54b4c3b3af8622",
    "7123952fbcc9abc787a6ea90e6e213f4fb1b47338c6d36b1e525864ff1131abf",
    "75e265fc4816d7416940f9094c716fdf849b9e2126ad82316d3e6a14cf56fc82",
    "7aea941a98d6cd3356f85fa3abec7039c41ccd538aa720763399af18a0422415",
    "8a28e93325a1d37a67667b027c4a48632eb88a1bb528aa94a1595ffd42728a34",
    "901845a1228a188bbd7a81f0610b2eae027af0439fcc1742134d7cab2fa6e985",
    "94ad9dae238467cb1857c640f1ae2e6d456a6ecba5cef50216aeb40cee84f385",
    "a264529ad71c5526c35e659c526d73c57feeb91a9f65eb9bb93bed0725a71763",
    "a6edb962b0751a645d2b8a4b4f1333029959555d3898ba39ceab183bfd36a056",
    "bb8a9583431d67aa688d54480ab7cedad409623614dbf5c635e47eaa0a767c76",
    "d40606f87b68e0cdaa6d794bf7a458ab4da360240eb2b55a1fdd3343db615dcf",
    "d991755d1cce2cf4e122089ebe43121444d54206a595a3c3a0656d992e05c399",
    "ec10bf6d65340b0289f05641bde60782c348735ca4f80646c1b01586841c9907",
    "ed206aaac908bc661cdea0b9ce8733dd858bb6c49a14716fa8da74b3a75c1004",
})


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


def find_block(text: str) -> tuple[int, int] | None:
    """공통 규칙 부분의 (시작, 끝) 위치. 표시가 둘 다 없으면 None, 한쪽만 있거나 순서가 틀리면 오류입니다."""
    start, end = text.find(BLOCK_START), text.find(BLOCK_END)
    if start < 0 and end < 0:
        return None
    if start < 0 or end < start or text.count(BLOCK_START) > 1 or text.count(BLOCK_END) > 1:
        raise ValueError(f"공통 규칙 표시({BLOCK_START} … {BLOCK_END})가 하나씩 순서대로 있지 않습니다. 직접 고친 뒤 다시 돌리세요")
    return start, end + len(BLOCK_END)


def extract_block(text: str) -> str:
    """시작·끝 표시를 포함한 공통 규칙 부분을 돌려줍니다."""
    span = find_block(text)
    if span is None:
        raise ValueError(f"공통 규칙 표시({BLOCK_START} … {BLOCK_END})를 찾지 못했습니다")
    return text[span[0] : span[1]]


def merge_block(existing: str, block: str) -> str:
    """기존 문서의 공통 규칙 부분만 바꿉니다. 표시가 둘 다 없으면 맨 아래에 붙입니다."""
    span = find_block(existing)
    if span is not None:
        return existing[: span[0]] + block + existing[span[1] :]
    body = existing.rstrip("\n")
    return f"{body}\n\n{block}\n" if body else f"{block}\n"


def imports_agents(claude_md: str) -> bool:
    return any(line.strip() in CLAUDE_IMPORT_LINES for line in claude_md.splitlines())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.is_file() else ""


def is_known_legacy(path: Path) -> bool:
    return hashlib.sha256(read_text(path).encode("utf-8")).hexdigest() in KNOWN_LEGACY_SHA256


def skill_files(source: Path, name: str) -> dict[str, bytes]:
    folder = source / ".agents" / "skills" / name
    if not folder.is_dir():
        raise ValueError(f"스킬 원본이 없습니다: {folder}")
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


class Planner:
    """바꿀 파일을 모읍니다. 내용이 같으면 바꾸지 않습니다."""

    def __init__(self) -> None:
        self.plan = Plan(changes=[], warnings=[])

    def _add(self, path: Path, content: bytes | None, note: str) -> None:
        self.plan.changes.append(Change(path, content, note))

    def write(self, path: Path, content: bytes) -> None:
        if path.is_file() and path.read_bytes() == content:
            self.plan.unchanged += 1
            return
        self._add(path, content, "바꿈" if path.exists() else "새로 만듦")

    def write_text(self, path: Path, text: str) -> None:
        """줄바꿈(CRLF/LF)만 다르면 같은 파일로 봅니다."""
        if path.is_file() and read_text(path) == text:
            self.plan.unchanged += 1
            return
        self.write(path, text.encode("utf-8"))

    def delete(self, path: Path, note: str) -> None:
        if path.is_file():
            self._add(path, None, note)

    def delete_legacy(self, path: Path, moved_to: str) -> None:
        """claude-home에 있던 내용 그대로인 예전 사본만 지웁니다."""
        if not path.is_file():
            return
        if is_known_legacy(path):
            self._add(path, None, f"지움 ({moved_to}로 옮겨짐)")
        else:
            self.warn(f"{path}: 예전 사본과 내용이 달라 지우지 않았습니다. 필요한 내용을 {moved_to}로 옮긴 뒤 직접 지우세요")

    def warn(self, message: str) -> None:
        self.plan.warnings.append(message)

    def copy_skill(self, source: Path, name: str, *skill_roots: Path) -> None:
        """스킬 폴더를 원본과 같게 맞춥니다. 원본에 없는 파일은 지웁니다."""
        files = skill_files(source, name)
        for root in skill_roots:
            for rel, content in files.items():
                self.write(root / name / rel, content)
            folder = root / name
            if folder.is_dir():
                for path in sorted(folder.rglob("*")):
                    if path.is_file() and path.relative_to(folder).as_posix() not in files:
                        self.delete(path, "지움 (원본 스킬에 없음)")


def plan_project(source: Path, target: Path, rule_sets: set[str]) -> Plan:
    """rule_sets: 넣을 언어 규칙과 번역 규칙("translation"). 이미 들어 있는 것은 저절로 갱신합니다."""
    block = extract_block(read_text(source / "AGENTS.md"))
    planner = Planner()

    agents = target / "AGENTS.md"
    existing = read_text(agents) or f"# {target.name}\n\n<!-- 저장소 안내(무엇인지, 명령어, 구조)를 여기에 적습니다. -->\n"
    planner.write_text(agents, merge_block(existing, block))

    claude = target / "CLAUDE.md"
    if not claude.is_file():
        planner.write_text(claude, f"{CLAUDE_IMPORT_LINES[0]}\n")
    elif not imports_agents(read_text(claude)):
        planner.warn(f"{claude}: `@AGENTS.md` 줄이 없어 Claude Code가 공통 규칙을 읽지 않습니다. 맨 위에 넣으세요")

    rules = target / ".claude" / "rules"
    installed = {lang for lang in LANGUAGES if (rules / "lang" / f"{lang}.md").is_file()}
    if (rules / "translation.md").is_file():
        installed.add(TRANSLATION)
    wanted = rule_sets | installed

    for name in COMMON_RULE_FILES:
        planner.write(rules / name, (source / ".claude/rules" / name).read_bytes())
    for lang in sorted(wanted & set(LANGUAGES)):
        planner.write(rules / "lang" / f"{lang}.md", (source / ".claude/rules/lang" / f"{lang}.md").read_bytes())
    skills = list(PROJECT_SKILLS)
    if TRANSLATION in wanted:
        planner.write(rules / "translation.md", (source / ".claude/rules/translation.md").read_bytes())
        skills += TRANSLATION_SKILLS
    for name in skills:
        planner.copy_skill(source, name, target / ".agents/skills", target / ".claude/skills")
        planner.delete_legacy(target / ".claude/commands" / f"{name}.md", f"스킬 {name}")

    for script in CHECK_SCRIPTS:
        planner.write(target / "scripts" / script, (source / "templates/ci" / script).read_bytes())
    for rel, template in AGENT_SETTINGS:
        settings = target / rel
        if not settings.is_file():
            planner.write(settings, (source / template).read_bytes())
        elif HOOK_SCRIPT_NAME not in read_text(settings):
            planner.warn(f"{settings}: 훅이 없습니다. claude-home의 {template}에서 hooks 부분을 합치세요")

    for name in LEGACY_RULE_FILES:
        planner.delete_legacy(rules / name, "AGENTS.md 위쪽 저장소 안내")
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
            planner.delete_legacy(claude_dir / "commands" / f"{folder.name}.md", f"스킬 {folder.name}")

    for name in LEGACY_RULE_FILES:
        planner.delete_legacy(claude_dir / "rules" / name, USER_RULES_FILE)
    return planner.plan


def plan_mirror(root: Path) -> Plan:
    """`.agents/skills/`(원본)를 `.claude/skills/`에 그대로 맞춥니다."""
    planner = Planner()
    source_dir = root / ".agents/skills"
    mirror_dir = root / ".claude/skills"
    names = {p.name for p in source_dir.iterdir() if p.is_dir()} if source_dir.is_dir() else set()
    for name in sorted(names):
        planner.copy_skill(root, name, mirror_dir)
    if mirror_dir.is_dir():
        for folder in sorted(p for p in mirror_dir.iterdir() if p.name not in names):
            paths = sorted(folder.rglob("*")) if folder.is_dir() else [folder]
            for path in paths:
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
    if not args.target and (args.lang or args.translation):
        parser.error("--lang, --translation은 --target과 함께 씁니다")
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.target:
            base = Path(args.target).resolve()
            if not base.is_dir():
                raise ValueError(f"프로젝트 폴더가 없습니다: {base}")
            rule_sets = set(args.lang) | ({TRANSLATION} if args.translation else set())
            plan = plan_project(SOURCE_ROOT, base, rule_sets)
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
