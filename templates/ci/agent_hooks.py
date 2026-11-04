#!/usr/bin/env python3
"""Claude Code와 Codex가 함께 쓰는 훅입니다. 같은 폴더(보통 scripts/)에 repo_checks.py와 함께 둡니다.

  pre-bash          셸 명령을 실행하기 전: 기본 브랜치(main, master)에 바로 커밋하거나 푸시하는 명령을 막습니다.
                    커밋이 하나도 없는 새 저장소의 첫 커밋과, 원격에 아직 그 브랜치가 없는 첫 푸시는 막지 않습니다.
  stop CHECK [...]  응답을 끝내기 전: 작업 트리에 바뀐 파일이 있으면 `python -I CHECK ...`를 저장소 루트에서 돌리고,
                    실패하면 끝내지 않고 고치게 합니다. 이미 한 번 막았으면(stop_hook_active) 다시 막지 않습니다.

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
# 셸 명령을 나누는 구분자. 따옴표 안의 구분자도 자르지만, 잘린 조각은 git 명령으로 보이지 않아 무시됩니다.
COMMAND_SEPARATORS = re.compile(r"&&|\|\||[;|\n]")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
GIT_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"})
PUSH_EVERYTHING = frozenset({"--all", "--mirror", "--branches"})
PUSH_OPTIONS_WITH_VALUE = frozenset({"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
DEFAULT_REMOTE = "origin"
BRANCH_RULE = "기본 브랜치에 바로 커밋·푸시하지 않습니다(공통 규칙: 브랜치와 PR). 작업 브랜치를 만들어 PR로 올리세요."


@dataclass(frozen=True)
class GitCall:
    directory: str | None  # git -C 로 준 폴더
    subcommand: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class RepoState:
    branch: str | None  # 분리된 HEAD면 None
    has_commits: bool
    remote_branches: frozenset[str] = frozenset()  # 이 저장소가 아는 원격 브랜치, 예: "origin/main"


def strip_heredoc(command: str) -> str:
    """heredoc 본문(예: 커밋 메시지)에 적힌 명령을 실제 명령으로 오해하지 않게 잘라 냅니다."""
    marker = command.find("<<")
    if marker < 0:
        return command
    line_end = command.find("\n", marker)
    return command if line_end < 0 else command[:line_end]


def git_calls(command: str) -> list[GitCall]:
    calls = []
    for segment in COMMAND_SEPARATORS.split(strip_heredoc(command)):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        while tokens and ENV_ASSIGNMENT.match(tokens[0]):
            tokens = tokens[1:]
        if not tokens or Path(tokens[0]).name.lower() not in ("git", "git.exe"):
            continue
        directory, index = None, 1
        while index < len(tokens) and tokens[index].startswith("-"):
            option = tokens[index]
            if option in GIT_OPTIONS_WITH_VALUE and index + 1 < len(tokens):
                directory = tokens[index + 1] if option == "-C" else directory
                index += 2
            else:
                index += 1
        if index < len(tokens):
            calls.append(GitCall(directory, tokens[index], tuple(tokens[index + 1 :])))
    return calls


def push_targets(args: tuple[str, ...], current_branch: str | None) -> tuple[str, set[str]]:
    """`git push`의 (원격 이름, 바꿀 원격 브랜치 이름들). 모든 브랜치를 올리는 옵션이면 기본 브랜치를 포함합니다."""
    positional, skip_next = [], False
    for arg in args:
        if skip_next:
            skip_next = False
        elif arg in PUSH_OPTIONS_WITH_VALUE:
            skip_next = True
        elif not arg.startswith("-"):
            positional.append(arg)
    remote = positional[0] if positional else DEFAULT_REMOTE
    if PUSH_EVERYTHING & set(args):
        return remote, set(PROTECTED_BRANCHES)
    refspecs = positional[1:]
    if not refspecs:
        return remote, {current_branch} if current_branch else set()
    targets = set()
    for refspec in refspecs:
        destination = refspec.lstrip("+").split(":", 1)[-1]
        if destination in ("HEAD", "@"):
            destination = current_branch or ""
        targets.add(destination.removeprefix("refs/heads/"))
    return remote, targets


def blocked_reason(call: GitCall, state: RepoState) -> str | None:
    if call.subcommand == "commit" and state.branch in PROTECTED_BRANCHES and state.has_commits:
        return f"`{state.branch}` 브랜치에 바로 커밋하려고 합니다. {BRANCH_RULE}"
    if call.subcommand == "push":
        remote, targets = push_targets(call.args, state.branch)
        # 원격에 아직 없는 기본 브랜치로 가는 첫 푸시(새 저장소 만들기)는 허용합니다.
        protected = {name for name in targets & PROTECTED_BRANCHES if f"{remote}/{name}" in state.remote_branches}
        if protected:
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


def stop(payload: dict, check: list[str]) -> int:
    if payload.get("stop_hook_active"):
        return EXIT_ALLOW
    root_text = git_output(Path(payload.get("cwd") or os.getcwd()), "rev-parse", "--show-toplevel")
    if not root_text or not check:
        return EXIT_ALLOW
    root = Path(root_text)
    if not (root / check[0]).is_file() or not git_output(root, "status", "--porcelain"):
        return EXIT_ALLOW  # 검사 도구가 없거나 바뀐 파일이 없으면 검사하지 않음
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
