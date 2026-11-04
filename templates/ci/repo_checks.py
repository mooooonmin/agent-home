#!/usr/bin/env python3
"""저장소 규칙을 한 번에 검사합니다. 로컬과 CI에서 같은 명령으로 돌립니다.

검사 항목:
- 생성 산출물 커밋: __pycache__, node_modules, .venv 등과 루트의 tmp/, logs/, outputs/ 같은 도구 출력 폴더
- 의존성 버전 고정: requirements*.txt의 모든 패키지가 `==`로 고정되었는지
- 변하는 이미지 태그: YAML·Dockerfile에서 `:latest` 사용
- 병합 충돌 표시: `<<<<<<< `, `>>>>>>> `로 시작하는 줄
- 셸 스크립트 문법: `bash -n` (bash가 없으면 건너뜀)
- 문서 내부 링크·이미지·앵커: check_doc_links.py
- 로컬 변경의 공백 오류: `git diff HEAD --check` (CI의 깨끗한 checkout에서는 할 일이 없음)
- 에이전트 지시 파일: AGENTS.md가 Codex 기본 읽기 한도(32KiB)를 넘는지, 같은 폴더의 CLAUDE.md가
  `@AGENTS.md`로 가져오는지, `.agents/skills/`(원본)와 `.claude/skills/`(사본)가 같은지
- 에이전트 훅 설정: `.claude/settings.json`, `.codex/hooks.json`이 가리키는 Python 스크립트가 있는지
  (없으면 python이 종료 코드 2로 끝나 두 도구 모두 훅이 "막음"으로 처리함)

표준 라이브러리만 씁니다. 이 파일과 check_doc_links.py를 같은 폴더(보통 scripts/)에 둡니다.

실행:  python3 -I scripts/repo_checks.py [--exclude 폴더 ...] [--docs-exclude 폴더 ...]
문제가 있으면 종료 코드 1로 끝납니다.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 어느 깊이에 있어도 생성물인 폴더
GENERATED_DIRS = {
    "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".gradle",
}
# 저장소 루트에 있을 때만 생성물로 보는 폴더 (src/app/logs/ 같은 소스 폴더와 구분)
GENERATED_TOP_DIRS = {"test-results", "coverage", "Claude outputs", "outputs", "tmp", "logs"}
GENERATED_SUFFIXES = {".pyc", ".pyo", ".class", ".log"}
REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*(\[[^\]]+\])?\s*==\s*[^\s;=]+(\s*;.*)?$")
LATEST_TAG = re.compile(r"(?:image:\s*\S+:latest\b|^\s*FROM\s+\S+:latest\b|\btag:\s*[\"']?latest[\"']?\s*$)", re.I)
CONFLICT = re.compile(r"^(<{7}|>{7}) ")
# Codex가 AGENTS.md를 읽는 기본 한도(project_doc_max_bytes). 루트부터 작업 폴더까지 합한 크기입니다.
CODEX_DOC_MAX_BYTES = 32 * 1024
SKILL_SOURCE_DIR = ".agents/skills/"
SKILL_MIRROR_DIR = ".claude/skills/"
HOOK_CONFIG_FILES = (".claude/settings.json", ".codex/hooks.json")
HOOK_SCRIPT = re.compile(r"[\w.-]+(?:/[\w.-]+)*\.py\b")
# Claude Code가 AGENTS.md를 가져오는 줄로 인정하는 형태
CLAUDE_IMPORT_LINES = ("@AGENTS.md", "@./AGENTS.md")
TEXT_SUFFIXES = {
    ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".dart", ".rs", ".sh",
    ".yml", ".yaml", ".json", ".toml", ".gradle", ".txt", ".html", ".css", ".xml", ".ps1",
}


def _load_doc_links():
    path = Path(__file__).with_name("check_doc_links.py")
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("check_doc_links", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_files(root: Path) -> list[str]:
    """추적 중이거나 새로 추가했지만 아직 커밋하지 않은 파일. ignored 파일은 뺍니다."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root, capture_output=True, check=True,
        ).stdout.decode("utf-8")
        files = [f for f in out.split("\0") if f]
    except (OSError, subprocess.CalledProcessError):
        files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    return sorted({f for f in files if (root / f).is_file()})


def excluded(rel: str, excludes: list[str]) -> bool:
    return any(rel == e or rel.startswith(e.rstrip("/") + "/") for e in excludes)


def read_lines(path: Path):
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []


def check_generated(files: list[str]) -> list[str]:
    errors = []
    for rel in files:
        parts = rel.split("/")
        in_generated_dir = any(p in GENERATED_DIRS for p in parts[:-1])
        in_top_generated_dir = len(parts) > 1 and parts[0] in GENERATED_TOP_DIRS
        if in_generated_dir or in_top_generated_dir or Path(rel).suffix in GENERATED_SUFFIXES:
            errors.append(f"{rel}: 생성 산출물은 커밋하지 않습니다 (.gitignore에 추가)")
    return errors


def check_pinned_requirements(root: Path, files: list[str]) -> list[str]:
    errors = []
    for rel in files:
        name = Path(rel).name
        if not (name.endswith(".txt") and "requirements" in name):
            continue
        for no, raw in enumerate(read_lines(root / rel), 1):
            line = raw.split(" #", 1)[0].strip()
            if not line or line.startswith(("#", "-")):
                continue
            if not REQUIREMENT.match(line):
                errors.append(f"{rel}:{no}: 버전을 ==로 고정합니다: {line}")
    return errors


def check_latest_tags(root: Path, files: list[str]) -> list[str]:
    errors = []
    for rel in files:
        name = Path(rel).name
        if not (name.endswith((".yml", ".yaml")) or name.startswith("Dockerfile")):
            continue
        for no, line in enumerate(read_lines(root / rel), 1):
            if LATEST_TAG.search(line):
                errors.append(f"{rel}:{no}: latest 태그 대신 고정 버전을 씁니다")
    return errors


def check_conflict_markers(root: Path, files: list[str]) -> list[str]:
    errors = []
    for rel in files:
        if Path(rel).suffix not in TEXT_SUFFIXES:
            continue
        for no, line in enumerate(read_lines(root / rel), 1):
            if CONFLICT.match(line):
                errors.append(f"{rel}:{no}: 병합 충돌 표시가 남아 있습니다")
    return errors


def check_shell_syntax(root: Path, files: list[str]) -> list[str]:
    scripts = [rel for rel in files if rel.endswith(".sh")]
    bash = shutil.which("bash")
    if not scripts or not bash:
        return []
    errors = []
    for rel in scripts:
        result = subprocess.run([bash, "-n", rel], cwd=root, capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            errors.append(f"{rel}: 셸 문법 오류: {result.stderr.strip()}")
    return errors


def check_doc_links(root: Path, excludes: list[str]) -> list[str]:
    module = _load_doc_links()
    if module is None:
        return []
    return [e for rel in module.list_markdown(str(root), excludes) for e in module.check(str(root), rel)]


def check_whitespace(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--check"], cwd=root, capture_output=True, text=True, encoding="utf-8"
        )
    except OSError:
        return []
    if result.returncode == 2 and result.stdout.strip():
        return [f"공백 오류(git diff HEAD --check): {line}" for line in result.stdout.splitlines() if line.strip()]
    return []


def check_agents_md_size(root: Path, files: list[str]) -> list[str]:
    docs = [rel for rel in files if Path(rel).name == "AGENTS.md"]
    sizes = {str(Path(rel).parent): (root / rel).stat().st_size for rel in docs}
    errors = []
    for rel in docs:
        folder = Path(rel).parent
        chain = [folder, *folder.parents]
        total = sum(sizes.get(str(level), 0) for level in chain)
        if total > CODEX_DOC_MAX_BYTES:
            errors.append(
                f"{rel}: 루트부터 이 폴더까지 AGENTS.md 합계 {total}바이트가 Codex 기본 한도 "
                f"{CODEX_DOC_MAX_BYTES}바이트를 넘어 뒷부분이 잘립니다 (자세한 내용은 담당 문서로 옮기고 링크)"
            )
    return errors


def check_claude_imports_agents(root: Path, files: list[str]) -> list[str]:
    """Claude Code는 작업 폴더나 그 위에 CLAUDE.md가 하나라도 있으면 AGENTS.md를 읽지 않습니다.

    그래서 그런 AGENTS.md마다 같은 폴더의 CLAUDE.md가 `@AGENTS.md`로 가져와야 합니다.
    """
    claude_dirs = {Path(rel).parent for rel in files if Path(rel).name == "CLAUDE.md"}
    errors = []
    for rel in files:
        if Path(rel).name != "AGENTS.md":
            continue
        folder = Path(rel).parent
        if not claude_dirs & {folder, *folder.parents}:
            continue  # CLAUDE.md가 없으면 Claude Code가 AGENTS.md를 직접 읽음
        claude = (folder / "CLAUDE.md").as_posix()
        if folder not in claude_dirs:
            errors.append(
                f"{rel}: 위쪽 폴더의 CLAUDE.md 때문에 Claude Code가 이 파일을 읽지 않습니다 "
                f"(같은 폴더에 `@AGENTS.md` 한 줄짜리 {claude} 추가)"
            )
        elif not any(line.strip() in CLAUDE_IMPORT_LINES for line in read_lines(root / claude)):
            errors.append(
                f"{claude}: CLAUDE.md가 있으면 Claude Code는 AGENTS.md를 읽지 않습니다 (맨 위에 `@AGENTS.md` 줄 추가)"
            )
    return errors


def check_skill_mirror(root: Path, files: list[str]) -> list[str]:
    source = {rel[len(SKILL_SOURCE_DIR):] for rel in files if rel.startswith(SKILL_SOURCE_DIR)}
    mirror = {rel[len(SKILL_MIRROR_DIR):] for rel in files if rel.startswith(SKILL_MIRROR_DIR)}
    if not source or not mirror:
        return []
    errors = []
    for rel in sorted(source | mirror):
        if rel not in mirror:
            errors.append(f"{SKILL_MIRROR_DIR}{rel}: 없습니다 (원본 {SKILL_SOURCE_DIR}{rel}을 그대로 복사)")
        elif rel not in source:
            errors.append(f"{SKILL_MIRROR_DIR}{rel}: 원본 {SKILL_SOURCE_DIR}{rel}이 없습니다 (원본에 만들거나 사본을 지움)")
        elif (root / SKILL_SOURCE_DIR / rel).read_bytes() != (root / SKILL_MIRROR_DIR / rel).read_bytes():
            errors.append(f"{SKILL_MIRROR_DIR}{rel}: 원본과 다릅니다 (원본 {SKILL_SOURCE_DIR}{rel}을 고친 뒤 그대로 복사)")
    return errors


def hook_command_strings(node, inside_hooks: bool = False):
    """설정 JSON에서 `hooks` 아래에 있는 문자열(명령과 인자)만 꺼냅니다."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from hook_command_strings(value, inside_hooks or key == "hooks")
    elif isinstance(node, list):
        for item in node:
            yield from hook_command_strings(item, inside_hooks)
    elif isinstance(node, str) and inside_hooks:
        yield node


def check_hook_scripts(root: Path, files: list[str]) -> list[str]:
    errors = []
    for rel in HOOK_CONFIG_FILES:
        if rel not in files:
            continue
        try:
            config = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"{rel}: JSON으로 읽을 수 없습니다 ({error})")
            continue
        scripts = {m.group(0) for text in hook_command_strings(config) for m in HOOK_SCRIPT.finditer(text)}
        for script in sorted(scripts):
            if not (root / script).is_file():
                errors.append(
                    f"{rel}: 훅 스크립트 {script}가 없습니다. 이대로면 셸 명령이 막히거나 훅이 돌지 않습니다 "
                    f"(claude-home의 sync_rules.py로 넣거나 훅 설정을 지움)"
                )
    return errors


def run_all(root: Path, excludes: list[str], docs_excludes: list[str] | None = None) -> list[str]:
    files = [f for f in list_files(root) if not excluded(f, excludes)]
    docs_excludes = excludes + (docs_excludes or [])
    return [
        *check_generated(files),
        *check_pinned_requirements(root, files),
        *check_latest_tags(root, files),
        *check_conflict_markers(root, files),
        *check_shell_syntax(root, files),
        *check_doc_links(root, docs_excludes),
        *check_whitespace(root),
        *check_agents_md_size(root, files),
        *check_claude_imports_agents(root, files),
        *check_skill_mirror(root, files),
        *check_hook_scripts(root, files),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="저장소 규칙 검사")
    parser.add_argument("--root", default=".", help="저장소 루트 (기본: 현재 폴더)")
    parser.add_argument("--exclude", nargs="*", default=[], help="모든 검사에서 뺄 폴더")
    parser.add_argument("--docs-exclude", nargs="*", default=[], help="문서 링크 검사에서만 뺄 폴더 (자리표시 링크가 많은 템플릿 등)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    errors = run_all(Path(args.root).resolve(), args.exclude, args.docs_exclude)
    for e in errors:
        print(e)
    print(f"저장소 검사: 문제 {len(errors)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
