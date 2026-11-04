#!/usr/bin/env python3
"""Claude Code와 Codex가 함께 쓰는 훅입니다. 같은 폴더(보통 scripts/)에 repo_checks.py와 함께 둡니다.

  pre-bash          셸 명령을 실행하기 전: 기본 브랜치(main, master)에 바로 커밋하거나 푸시하는 명령을 막습니다.
                    앞선 cd, git -C, sh -c, $(...)를 따라가고 heredoc 본문은 건너뜁니다. 커밋이 하나도 없는 새 저장소의
                    첫 커밋과, 원격 브랜치를 하나도 모르는 새 저장소의 첫 푸시는 막지 않습니다.
                    셸 문장을 읽어 판단하는 보조 장치라 완벽하지 않습니다. GitHub 저장소 규칙으로도 기본 브랜치를 보호하세요.
  stop CHECK [...]  응답을 끝내기 전: 커밋하지 않은 변경이나 올리지 않은 커밋이 있으면 `python -I CHECK ...`를
                    저장소 루트에서 돌리고, 실패하면 끝내지 않고 고치게 합니다. 이미 한 번 막았으면(stop_hook_active)
                    다시 막지 않습니다.

두 도구 모두 훅 입력(JSON)을 표준 입력으로 주고, 종료 코드 2와 표준 오류의 이유를 "막기"로 처리합니다.
훅 자체가 망가져도(입력이 JSON이 아님, git 없음) 작업을 막지 않도록 그때는 0으로 끝냅니다.
표준 라이브러리만 씁니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROTECTED_BRANCHES = frozenset({"main", "master"})
EXIT_ALLOW = 0
EXIT_BLOCK = 2
# heredoc 시작(`<<EOF`, `<<-'EOF'`). here-string(`<<<`)은 제외합니다.
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
SHELL_PUNCTUATION = "();<>|&"
SEGMENT_BREAK_CHARS = set(";&|()")
FALLBACK_SEPARATORS = re.compile(r"&&|\|\||[;|&\n()]")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
DIRECTORY_COMMANDS = frozenset({"cd", "pushd"})
NESTED_SHELLS = frozenset({"sh", "bash", "zsh", "dash"})
GIT_PROGRAMS = frozenset({"git", "git.exe"})
GIT_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"})
PUSH_EVERYTHING = frozenset({"--all", "--mirror", "--branches"})
PUSH_OPTIONS_WITH_VALUE = frozenset({"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
BRANCH_RULE = "기본 브랜치에 바로 커밋·푸시하지 않습니다(공통 규칙: 브랜치와 PR). 작업 브랜치를 만들어 PR로 올리세요."


@dataclass(frozen=True)
class GitCall:
    directory: str | None  # 앞선 cd와 git -C 로 바뀐 폴더(훅 cwd 기준). 그대로면 None
    subcommand: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class RepoState:
    branch: str | None  # 분리된 HEAD면 None
    has_commits: bool
    remote_branches: frozenset[str] = frozenset()  # 이 저장소가 아는 원격 브랜치, 예: "origin/main"


def strip_heredocs(command: str) -> str:
    """heredoc 본문(예: 커밋 메시지)만 지우고, 끝 표시 뒤의 명령은 남깁니다."""
    lines = command.split("\n")
    kept, index = [], 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        for match in HEREDOC.finditer(line):  # 한 줄에 heredoc이 여럿이면 본문이 차례로 옴
            terminator = match.group(2)
            while index < len(lines) and lines[index].strip() != terminator:
                index += 1
            index += 1  # 끝 표시 줄
    return "\n".join(kept)


def newlines_to_separators(command: str) -> str:
    """따옴표 밖의 줄바꿈을 `;`로 바꿔, 여러 줄 명령을 명령 단위로 나눌 수 있게 합니다."""
    out, quote, escaped = [], None, False
    for char in command:
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            quote = None if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char == "\n":
            char = ";"
        out.append(char)
    return "".join(out)


def is_segment_break(token: str) -> bool:
    return all(c in SHELL_PUNCTUATION for c in token) and bool(SEGMENT_BREAK_CHARS & set(token))


def command_segments(command: str) -> list[list[str]]:
    """명령을 `;`, `&&`, `||`, `|`, `&`, 괄호, 줄바꿈 단위로 나눈 토큰 목록. 따옴표 안은 나누지 않습니다."""
    text = strip_heredocs(command)
    lexer = shlex.shlex(newlines_to_separators(text), posix=True, punctuation_chars=SHELL_PUNCTUATION)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # 따옴표가 닫히지 않은 명령은 단순하게 나눔
        return [part.split() for part in FALLBACK_SEPARATORS.split(text) if part.split()]
    segments, current = [], []
    for token in tokens:
        if is_segment_break(token):
            segments.append(current)
            current = []
        else:
            current.append(token)
    segments.append(current)
    return [segment for segment in segments if segment]


def join_directory(base: str | None, path: str) -> str:
    return path if base is None else os.path.join(base, path)  # 절대 경로면 path가 그대로 남음


def git_calls(command: str, directory: str | None = None) -> list[GitCall]:
    calls = []
    for tokens in command_segments(command):
        while tokens and ENV_ASSIGNMENT.match(tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        program = Path(tokens[0]).name.lower()
        if program in DIRECTORY_COMMANDS and len(tokens) > 1:
            directory = join_directory(directory, tokens[1])
            continue
        if program in NESTED_SHELLS and len(tokens) > 2 and tokens[1] == "-c":
            calls += git_calls(tokens[2], directory)
            continue
        if program not in GIT_PROGRAMS:
            continue
        target, index = directory, 1
        while index < len(tokens) and tokens[index].startswith("-"):
            option = tokens[index]
            if option in GIT_OPTIONS_WITH_VALUE and index + 1 < len(tokens):
                target = join_directory(target, tokens[index + 1]) if option == "-C" else target
                index += 2
            else:
                index += 1
        if index < len(tokens):
            calls.append(GitCall(target, tokens[index], tuple(tokens[index + 1 :])))
    return calls


def push_targets(args: tuple[str, ...], current_branch: str | None) -> set[str]:
    """`git push`가 바꿀 원격 브랜치 이름들. 모든 브랜치를 올리는 옵션이면 기본 브랜치를 포함합니다."""
    if PUSH_EVERYTHING & set(args):
        return set(PROTECTED_BRANCHES)
    positional, skip_next = [], False
    for arg in args:
        if skip_next:
            skip_next = False
        elif arg in PUSH_OPTIONS_WITH_VALUE:
            skip_next = True
        elif not arg.startswith("-"):
            positional.append(arg)
    refspecs = positional[1:]  # 첫 번째는 원격 이름이나 주소
    if not refspecs:
        return {current_branch} if current_branch else set()
    targets = set()
    for refspec in refspecs:
        destination = refspec.lstrip("+").split(":", 1)[-1]
        if destination in ("HEAD", "@"):
            destination = current_branch or ""
        targets.add(destination.removeprefix("refs/heads/"))
    return targets


def blocked_reason(call: GitCall, state: RepoState) -> str | None:
    if call.subcommand == "commit" and state.branch in PROTECTED_BRANCHES and state.has_commits:
        return f"`{state.branch}` 브랜치에 바로 커밋하려고 합니다. {BRANCH_RULE}"
    if call.subcommand == "push":
        protected = push_targets(call.args, state.branch) & PROTECTED_BRANCHES
        # 원격 브랜치를 하나도 모르는 저장소(방금 만든 새 저장소)의 첫 푸시만 허용합니다.
        # 원격 이름·주소와 관계없이 판단해, 일부 브랜치만 받은 clone에서도 막히게 합니다.
        if protected and state.remote_branches:
            return f"`{', '.join(sorted(protected))}` 브랜치로 바로 푸시하려고 합니다. {BRANCH_RULE}"
    return None


def git_output(directory: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=directory, capture_output=True, text=True, encoding="utf-8", check=False
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def read_repo_state(directory: Path) -> RepoState:
    return RepoState(
        branch=git_output(directory, "symbolic-ref", "--quiet", "--short", "HEAD"),
        has_commits=git_output(directory, "rev-parse", "--verify", "--quiet", "HEAD") is not None,
        remote_branches=frozenset(
            (git_output(directory, "for-each-ref", "--format=%(refname:short)", "refs/remotes") or "").split()
        ),
    )


def pre_bash(payload: dict) -> int:
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return EXIT_ALLOW
    cwd = Path(payload.get("cwd") or os.getcwd())
    for call in git_calls(command):
        if call.subcommand not in ("commit", "push"):
            continue
        directory = cwd / call.directory if call.directory else cwd
        reason = blocked_reason(call, read_repo_state(directory))
        if reason:
            print(reason, file=sys.stderr)
            return EXIT_BLOCK
    return EXIT_ALLOW


def has_unfinished_work(root: Path) -> bool:
    """커밋하지 않은 변경이나, 어느 원격에도 올리지 않은 커밋이 있는지."""
    if git_output(root, "status", "--porcelain"):
        return True
    unpushed = git_output(root, "rev-list", "--count", "HEAD", "--not", "--remotes")
    return bool(unpushed) and unpushed != "0"


def stop(payload: dict, check: list[str]) -> int:
    if payload.get("stop_hook_active"):
        return EXIT_ALLOW
    root_text = git_output(Path(payload.get("cwd") or os.getcwd()), "rev-parse", "--show-toplevel")
    if not root_text or not check:
        return EXIT_ALLOW
    root = Path(root_text)
    if not (root / check[0]).is_file() or not has_unfinished_work(root):
        return EXIT_ALLOW  # 검사 도구가 없거나, 바뀐 것도 올리지 않은 커밋도 없으면 검사하지 않음
    result = subprocess.run(
        [sys.executable, "-I", *check], cwd=root, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode == 0:
        return EXIT_ALLOW
    print(
        f"끝내기 전에 돌린 저장소 검사(python -I {' '.join(check)})가 실패했습니다. 고친 뒤 마무리하세요. "
        f"이번 변경과 상관없는 문제라면 그렇다고 보고하세요.\n{result.stdout}{result.stderr}",
        file=sys.stderr,
    )
    return EXIT_BLOCK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code·Codex 공통 훅")
    commands = parser.add_subparsers(dest="hook", required=True)
    commands.add_parser("pre-bash", help="셸 명령 실행 전 검사")
    stop_parser = commands.add_parser("stop", help="응답을 끝내기 전 저장소 검사")
    stop_parser.add_argument("check", nargs=argparse.REMAINDER, help="python -I 로 돌릴 검사 스크립트와 인자")
    args = parser.parse_args(argv)
    if hasattr(sys.stderr, "reconfigure"):  # Windows 콘솔에서도 한국어 이유가 깨지지 않게
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return EXIT_ALLOW
    if not isinstance(payload, dict):
        return EXIT_ALLOW
    if args.hook == "pre-bash":
        return pre_bash(payload)
    return stop(payload, args.check)


if __name__ == "__main__":
    sys.exit(main())
