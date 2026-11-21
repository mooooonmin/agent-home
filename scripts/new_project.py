#!/usr/bin/env python3
"""agent-home의 규칙·검사·문서 틀을 깐 새 프로젝트 폴더를 만듭니다.

기본은 미리보기입니다. 만들 파일만 보여 주고, --apply를 붙여야 실제로 만듭니다.

  python -I scripts/new_project.py --name my-app --language python --description "할 일 목록 CLI"
  python -I scripts/new_project.py --name my-app --language python --description "할 일 목록 CLI" --apply

- 새 폴더는 --path(기본: agent-home이 있는 폴더) 아래 --name으로 만듭니다. 비어 있지 않은 폴더면 멈춥니다.
- 언어별 뼈대(코드, 빌드 파일)는 만들지 않습니다. 각 언어의 공식 도구로 만듭니다(new-project 스킬 참고).
- 공통 규칙·언어 규칙·스킬·검사·훅 스크립트와 훅 설정은 sync_rules.py와 같은 함수로 넣습니다.
- --translation을 붙이면 번역 저장소용 규칙·스킬과 TRANSLATION.md도 넣습니다.

표준 라이브러리만 씁니다.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DESCRIPTION_PLACEHOLDER = "<이 저장소가 무엇인지 한두 문장>"
LEADING_COMMENT = re.compile(r"\A<!--.*?-->\n\n", re.S)
TRANSLATION_LINE = re.compile(r"- 번역 저장소라면: [^\n]*\n")


def _load_sync_rules():
    # -I(격리 모드)에서는 스크립트 폴더가 import 경로에 없어 파일 위치로 불러옵니다.
    spec = importlib.util.spec_from_file_location("sync_rules", Path(__file__).with_name("sync_rules.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_rules"] = module  # dataclass가 모듈을 찾을 수 있게 등록
    spec.loader.exec_module(module)
    return module


sync_rules = _load_sync_rules()


@dataclass(frozen=True)
class LanguageSetup:
    lint_files: tuple[tuple[str, str], ...]  # (templates/lint 안의 경로, 프로젝트 안의 경로)
    commands: str  # AGENTS.md의 명령어 칸에 넣을 포맷·린트·테스트 명령
    gitignore: str  # .gitignore에 덧붙일 줄


LANGUAGE_SETUPS = {
    "java": LanguageSetup(
        (),
        "./gradlew spotlessApply   # 포맷\n./gradlew test            # 테스트(ArchUnit 포함)\n./gradlew build           # 전체 빌드",
        "out/\n*.iml\nbin/",
    ),
    "python": LanguageSetup(
        (("python/ruff.toml", "ruff.toml"),),
        "ruff format .              # 포맷\nruff check --fix .         # 린트\npytest                     # 테스트",
        "*.egg-info/\n.coverage\nhtmlcov/",
    ),
    "typescript": LanguageSetup(
        (("typescript/eslint.config.js", "eslint.config.js"), ("typescript/.prettierrc.json", ".prettierrc.json")),
        "npx prettier --write .     # 포맷\nnpx eslint .               # 린트\nnpx tsc --noEmit           # 타입 검사\n"
        "npm test                   # 테스트",
        ".next/\n*.tsbuildinfo\n.turbo/",
    ),
    "dart": LanguageSetup(
        (("dart/analysis_options.yaml", "analysis_options.yaml"),),
        "dart format .              # 포맷\nflutter analyze            # 린트\nflutter test               # 테스트",
        ".dart_tool/\n.flutter-plugins\n.flutter-plugins-dependencies\n*.iml\n.metadata",
    ),
    "go": LanguageSetup(
        (("go/.golangci.yml", ".golangci.yml"),),
        "gofmt -w . && goimports -w .   # 포맷\ngolangci-lint run              # 린트\ngo test -race ./...            # 테스트",
        "/bin/\n*.test\ncoverage.out",
    ),
}


@dataclass(frozen=True)
class ProjectRequest:
    name: str
    language: str
    description: str
    translation: bool  # 번역 저장소면 번역 규칙·스킬·TRANSLATION.md도 넣음
    target: Path

    @property
    def rule_sets(self) -> set[str]:
        """sync_rules.plan_project에 넘길 규칙 묶음."""
        return {self.language} | ({sync_rules.TRANSLATION} if self.translation else set())


def read_template(source: Path, rel: str) -> str:
    return (source / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def agents_md(source: Path, request: ProjectRequest) -> str:
    text = LEADING_COMMENT.sub("", read_template(source, "templates/AGENTS.project.md"), count=1)
    text = text.replace("<저장소 이름>", request.name).replace(DESCRIPTION_PLACEHOLDER, request.description)
    commands = f"{LANGUAGE_SETUPS[request.language].commands}\npython -I scripts/repo_checks.py   # 저장소 규칙 검사"
    text = text.replace("<테스트>\n<포맷·린트>", commands)
    if not request.translation:
        text = TRANSLATION_LINE.sub("", text)
    block = sync_rules.extract_block(read_template(source, "AGENTS.md"))
    return sync_rules.merge_block(text, block)


def fill(text: str, replacements: dict[str, str]) -> str:
    """템플릿의 자리표시를 바꿉니다. 템플릿 모양이 바뀌어 자리표시가 없으면 멈춥니다(테스트가 잡도록)."""
    for old, new in replacements.items():
        if old not in text:
            raise ValueError(f"템플릿에서 바꿀 부분을 찾지 못했습니다: {old!r}")
        text = text.replace(old, new)
    return text


def exec_plans_readme(source: Path, today: str) -> str:
    template = read_template(source, "templates/docs/exec-plans/README.md")
    return fill(template, {
        "| [<제목>](active/<파일>.md) | <한 줄> | YYYY-MM-DD |":
            f"| [초기 구축](active/0001-initial-setup.md) | 뼈대, 검사, 문서를 갖춘 첫 동작 버전 | {today} |",
        "| 기록 | 범위 | 근거 |\n|---|---|---|\n| [<제목>](completed/<파일>.md) | <한 줄> | 커밋 `<sha>` |":
            "아직 없습니다.",
        # 새 프로젝트에는 아직 개선 목록 파일이 없어 링크가 깨지지 않게 이름만 둡니다.
        "[tech-debt-tracker.md](tech-debt-tracker.md)에 적습니다": "`tech-debt-tracker.md`를 만들어 적습니다",
    })


def initial_plan(request: ProjectRequest, today: str) -> str:
    return f"""# 초기 구축

- 상태: 진행 중
- 시작: {today}
- 관련: 없음

## 목표

{request.description}

뼈대, 검사, 문서를 갖추고 CI가 통과하는 첫 동작 버전을 만듭니다.

## 현재 상태

다음 세션이 이 부분만 읽고 이어 갈 수 있게, 세션을 끝낼 때마다 덮어씁니다.

- 마지막 커밋: 없음
- 검사·테스트: 미확인
- 진행 중: 1단계
- 다음 할 일: 언어 공식 도구로 뼈대 생성
- 막힌 것: 없음

## 범위

- 하는 것: 언어 공식 도구로 뼈대 생성, 린트·포맷·계층 검사 적용, README·AGENTS.md 채우기, 기술 선택 ADR, 첫 기능 하나
- 안 하는 것: <이번에 하지 않을 것>

## 단계

- [ ] 1. 언어 공식 도구로 뼈대 생성 — 완료 조건: 빌드·테스트 명령이 로컬에서 동작
- [ ] 2. 린트·포맷·계층 검사 설정 적용 — 완료 조건: 포맷·린트 명령이 통과
- [ ] 3. 기술 선택을 `docs/adr/0001-*.md`로 기록 — 완료 조건: 채택 상태의 ADR
- [ ] 4. README 시작하기와 AGENTS.md 명령어·동작 확인·구조 채우기 — 완료 조건: 자리표시(`<...>`) 없음
- [ ] 5. 첫 기능 하나와 테스트 — 완료 조건: 테스트 통과
- [ ] 6. GitHub 저장소에 올리고 CI 통과 — 완료 조건: `checks`와 `{request.language}` 워크플로 성공

## 완료 조건

- 로컬과 CI에서 저장소 검사, 포맷·린트, 테스트가 모두 통과합니다.

## 검증

| 확인 | 명령·방법 | 결과 |
|---|---|---|
| 저장소 규칙 | `python -I scripts/repo_checks.py` | 미확인 |
| 훅 | 기본 브랜치에서 `git commit --dry-run --allow-empty -m 확인`이 막히는지 | 미확인 |
| 언어 검사·테스트 | AGENTS.md의 명령어 | 미확인 |
| CI | GitHub Actions | 미확인 |

## 결정과 남은 문제

-

## 완료 기록

"""


def base_files(source: Path, request: ProjectRequest, today: str) -> dict[str, str]:
    """sync_rules.py가 넣지 않는, 새 프로젝트에만 한 번 만드는 파일들 (프로젝트 안 경로 → 내용)."""
    setup = LANGUAGE_SETUPS[request.language]
    copies = {
        ".editorconfig": "templates/lint/.editorconfig",
        ".gitattributes": "templates/lint/.gitattributes",
        ".github/workflows/checks.yml": "templates/ci/checks.yml",
        f".github/workflows/{request.language}.yml": f"templates/ci/lang/{request.language}.yml",
        ".github/pull_request_template.md": ".github/pull_request_template.md",
        "CLAUDE.md": "templates/CLAUDE.project.md",
        "CHANGELOG.md": "templates/docs/CHANGELOG.md",
        "docs/adr/template.md": "templates/docs/adr/0001-template.md",
        "docs/exec-plans/plan-template.md": "templates/docs/exec-plans/plan-template.md",
        **{dst: f"templates/lint/{src}" for src, dst in setup.lint_files},
    }
    if request.translation:
        copies["TRANSLATION.md"] = "templates/translation-repo/TRANSLATION.md"
    files = {dst: read_template(source, src) for dst, src in copies.items()}
    files[".gitignore"] = f"{read_template(source, 'templates/lint/.gitignore')}\n# {request.language}\n{setup.gitignore}\n"
    files[".env.example"] = "# 필요한 환경 변수를 값 없이 적습니다. 실제 값은 .env(커밋하지 않음)나 CI 비밀값에 둡니다.\n"
    files["AGENTS.md"] = agents_md(source, request)
    readme = read_template(source, "templates/docs/README.md")
    files["README.md"] = readme.replace("<프로젝트 이름>", request.name).replace(
        "<무엇을 하는 프로젝트인지 한두 문장>", request.description
    )
    files["docs/exec-plans/README.md"] = exec_plans_readme(source, today)
    files["docs/exec-plans/active/0001-initial-setup.md"] = initial_plan(request, today)
    return files


def base_plan(source: Path, request: ProjectRequest, today: str) -> sync_rules.Plan:
    changes = [
        sync_rules.Change(request.target / rel, text.encode("utf-8"), "새로 만듦")
        for rel, text in sorted(base_files(source, request, today).items())
    ]
    return sync_rules.Plan(changes=changes, warnings=[])


def check_target(target: Path) -> None:
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError(f"이미 비어 있지 않은 폴더입니다: {target}")


def git_init(target: Path) -> str | None:
    """경고 문구를 돌려줍니다. 성공하면 None."""
    # `git init -b`는 Git 2.28 이상이라, 오래된 git에서도 되는 init + symbolic-ref로 main을 정합니다.
    for command in (["git", "init", "-q"], ["git", "symbolic-ref", "HEAD", "refs/heads/main"]):
        try:
            result = subprocess.run(command, cwd=target, capture_output=True, text=True)
        except OSError as error:
            return f"git을 실행하지 못했습니다({error}). 직접 실행하세요: git -C \"{target}\" init -b main"
        if result.returncode:
            return (f"{' '.join(command)}이 실패했습니다({result.stderr.strip()}). 경로가 너무 길지 않은지 확인하고 "
                    f"직접 실행하세요: git -C \"{target}\" init -b main")
    return None


def preview(source: Path, request: ProjectRequest, today: str) -> sync_rules.Plan:
    """폴더를 만들지 않고 만들 파일을 모읍니다. sync_rules.py가 넣을 파일 중 겹치는 것은 뺍니다."""
    plan = base_plan(source, request, today)
    planned = {change.path for change in plan.changes}
    synced = sync_rules.plan_project(source, request.target, request.rule_sets)
    plan.changes += [change for change in synced.changes if change.path not in planned]
    return plan


def create(source: Path, request: ProjectRequest, today: str) -> sync_rules.Plan:
    check_target(request.target)
    plan = base_plan(source, request, today)  # 템플릿을 모두 읽은 뒤에 쓰기 시작해, 템플릿 문제로 반쯤 만들어지지 않게 함
    try:
        sync_rules.apply(plan)
        warning = git_init(request.target)
        synced = sync_rules.plan_project(source, request.target, request.rule_sets)
        sync_rules.apply(synced)
    except (ValueError, OSError) as error:
        raise ValueError(f"만들다 멈췄습니다({error}). {request.target} 폴더를 지운 뒤 다시 실행하세요") from error
    plan.changes += synced.changes
    plan.unchanged += synced.unchanged
    plan.warnings += synced.warnings + ([warning] if warning else [])
    return plan


def parse_request(argv: list[str] | None) -> tuple[ProjectRequest, bool]:
    parser = argparse.ArgumentParser(description="agent-home 기준 새 프로젝트 만들기")
    parser.add_argument("--name", required=True, help="프로젝트(폴더) 이름: 영문·숫자·.-_")
    parser.add_argument("--language", required=True, choices=sorted(LANGUAGE_SETUPS))
    parser.add_argument("--description", default=DESCRIPTION_PLACEHOLDER, help="이 저장소가 무엇인지 한두 문장")
    parser.add_argument("--path", help="새 폴더를 만들 상위 폴더 (기본: agent-home이 있는 폴더)")
    parser.add_argument("--translation", action="store_true", help="번역 저장소용 규칙·스킬·TRANSLATION.md도 넣기")
    parser.add_argument("--apply", action="store_true", help="실제로 만듭니다. 없으면 미리보기만 합니다")
    args = parser.parse_args(argv)
    if not NAME_PATTERN.match(args.name):
        parser.error(f"--name은 영문·숫자로 시작하고 영문·숫자·.-_만 씁니다: {args.name}")
    parent = Path(args.path).resolve() if args.path else SOURCE_ROOT.parent
    request = ProjectRequest(args.name, args.language, args.description, args.translation, parent / args.name)
    return request, args.apply


def main(argv: list[str] | None = None) -> int:
    request, should_apply = parse_request(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    today = datetime.date.today().isoformat()
    try:
        check_target(request.target)
        plan = create(SOURCE_ROOT, request, today) if should_apply else preview(SOURCE_ROOT, request, today)
    except (ValueError, OSError) as error:
        print(f"새 프로젝트를 만들지 못했습니다: {error}", file=sys.stderr)
        return 1

    if should_apply:
        sync_rules.report(plan, request.target, f"만듦: {request.target}, 파일")
        print("다음 단계:")
        print(f"  1. {request.language} 공식 도구로 뼈대 만들기 (기존 파일을 덮어쓰지 않게)")
        print("  2. docs/exec-plans/active/0001-initial-setup.md의 단계를 따라 진행")
        print("  3. 검사: python -I scripts/repo_checks.py")
    else:
        sync_rules.report(plan, request.target, f"미리보기 (--apply를 붙이면 실제로 만듭니다): {request.target}, 파일")
    return 0


if __name__ == "__main__":
    sys.exit(main())
