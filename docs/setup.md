# 초기 설정

claude-home을 처음 받아서 로컬 PC와 클라우드 세션에서 쓰기까지의 순서입니다. 처음 한 번만 하면 되고, 다른 PC에서도 같은 순서로 합니다.

## 한눈에 보기

1. [필요한 도구 설치](#1-필요한-도구-설치)
2. [저장소 받기](#2-저장소-받기)
3. [로컬 PC에 규칙 적용](#3-로컬-pc에-규칙-적용)
4. [설정 확인](#4-설정-확인)
5. [클라우드 세션 설정](#5-클라우드-세션-설정)

그다음은 [새 프로젝트 시작하기](../README.md#새-프로젝트-시작하기)나 [기존 프로젝트에 적용하기](../README.md#기존-프로젝트에-적용하기)로 넘어갑니다.

## 1. 필요한 도구 설치

| 도구 | 쓰는 곳 | 확인 명령 | 설치 (Windows) |
|---|---|---|---|
| Git | 저장소 받기, 커밋 | `git --version` | `winget install Git.Git` |
| GitHub CLI | 저장소 받기·만들기, PR | `gh --version` | `winget install GitHub.cli` |
| PowerShell 7 | `scripts/*.ps1` 실행 | `pwsh --version` | `winget install Microsoft.PowerShell` |
| Python 3.11 이상 | 저장소 검사 스크립트 | `python --version` | `winget install Python.Python.3.12` |
| Claude Code | 규칙과 명령어 사용 | 데스크톱 앱 또는 `claude --version` | [Claude Code 문서](https://code.claude.com/docs) |

Windows에 기본으로 있는 PowerShell 5(`powershell`)가 아니라 **PowerShell 7(`pwsh`)** 이 필요합니다.

설치 후 GitHub에 로그인합니다.

```bash
gh auth login
```

```bash
gh auth status
```

## 2. 저장소 받기

다른 프로젝트들과 **같은 상위 폴더**에 받습니다. `/new-project`는 claude-home 옆에 새 프로젝트를 만들기 때문입니다.

```bash
gh repo clone mooooonmin/claude-home C:/00.PROJECT/claude-home
```

## 3. 로컬 PC에 규칙 적용

규칙과 명령어를 `~/.claude/`로 복사하면 이 PC의 **모든 프로젝트**에서 Claude Code가 같은 규칙을 따릅니다. 먼저 미리보기로 복사할 파일을 확인합니다.

```bash
pwsh -File C:/00.PROJECT/claude-home/scripts/sync-local.ps1 -WhatIf
```

문제없으면 실제로 복사합니다.

```bash
pwsh -File C:/00.PROJECT/claude-home/scripts/sync-local.ps1
```

| 복사되는 것 | 위치 | 효과 |
|---|---|---|
| `.claude/rules/` | `~/.claude/rules/` | 모든 프로젝트에 규칙 적용 (언어별 규칙은 해당 언어 파일을 다룰 때만) |
| `.claude/commands/` | `~/.claude/commands/` | 어느 프로젝트에서나 `/update-docs`, `/new-project` 등을 쓸 수 있음 |

- 같은 이름의 파일은 덮어쓰고, `~/.claude/`에만 있는 파일은 지우지 않습니다.
- claude-home 안에서 작업하면 같은 규칙이 두 번(개인 설정 + 저장소) 읽힙니다. 내용이 같아서 문제는 없습니다.
- 번역 규칙(`translation.md`)도 복사되지만 `.md`, `.ipynb` 파일을 다룰 때만 읽히고, 저장소에 `TRANSLATION.md`가 있으면 그쪽이 우선합니다.

## 4. 설정 확인

모두 통과하면 설정이 끝난 것입니다.

| 확인 | 명령·방법 | 기대 결과 |
|---|---|---|
| 규칙 복사 | `ls ~/.claude/rules ~/.claude/commands` | `basics.md`, `coding.md`, `new-project.md` 등이 보임 |
| 검사 도구 | claude-home에서 `python -I -m unittest discover -s templates/ci -p "test_*.py"` | `OK` |
| 저장소 검사 | claude-home에서 `python -I templates/ci/repo_checks.py --docs-exclude templates` | `문제 0개` |
| 새 프로젝트 미리보기 | claude-home에서 `pwsh -File scripts/new-project.ps1 -Name test-app -Language python -WhatIf` | 만들 파일 목록만 나오고 폴더는 생기지 않음 |
| 규칙 적용 | 아무 프로젝트에서 Claude Code를 열고 "지금 적용된 규칙 파일 목록 알려줘"라고 묻기 | `~/.claude/rules/`의 파일들이 언급됨 |

## 5. 클라우드 세션 설정

클라우드 세션은 별도 가상 머신에서 돌아서 내 PC를 꺼도 계속 작업합니다. 대신 **세션을 시작할 때 고른 저장소 하나만** 보고, 내 PC의 `~/.claude/` 설정은 따라가지 않습니다. 그래서 규칙이 저장소 안에 있어야 합니다.

1. [claude.ai/code](https://claude.ai/code)에서 GitHub 계정을 연결합니다.
2. 세션을 시작할 때 저장소를 고릅니다.
   - 조사·메모 같은 일반 작업: `claude-home` (결과는 `notes/`에 저장)
   - 특정 프로젝트 작업: 그 프로젝트 저장소. 저장소에 `.claude/rules/`와 `CLAUDE.md`가 있어야 규칙이 적용됩니다. `/new-project`로 만든 프로젝트는 이미 들어 있습니다.
3. API 키 같은 비밀값이 필요하면 저장소가 아니라 클라우드 세션의 **환경 설정**에 환경 변수로 등록합니다.
4. 크레딧과 사용량은 Claude 설정의 사용량 화면에서 확인합니다.

화면 이름과 위치는 바뀔 수 있으니 막히면 [Claude Code 문서](https://code.claude.com/docs)를 확인합니다.

## 규칙을 고친 뒤

claude-home이 규칙의 원본입니다. 규칙은 항상 여기서 고치고 다른 곳으로 퍼뜨립니다.

1. claude-home에서 작업 브랜치를 만들어 고치고, PR로 `main`에 병합합니다.
2. 이 PC에 반영합니다.
   ```bash
   git -C C:/00.PROJECT/claude-home pull
   ```
   ```bash
   pwsh -File C:/00.PROJECT/claude-home/scripts/sync-local.ps1
   ```
3. 클라우드에서 쓰는 프로젝트에는 바뀐 규칙 파일을 그 저장소의 `.claude/rules/`로 복사해 커밋합니다. 자동으로 따라가지 않습니다.
4. 다른 PC에서는 2번만 하면 됩니다.

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `pwsh`를 찾을 수 없음 | PowerShell 7이 없음 | `winget install Microsoft.PowerShell` 후 터미널을 새로 엶 |
| 스크립트 실행이 막힘 (`running scripts is disabled`) | 실행 정책 | `pwsh -ExecutionPolicy Bypass -File <스크립트>`로 그 실행만 허용 |
| `git init`이 실패했다는 경고 (`Filename too long`) | Windows 경로 길이 제한(260자) | 더 짧은 경로에 만들거나 `git config --global core.longpaths true` |
| 한글이 깨져 보임 | 터미널 인코딩 | PowerShell 7을 쓰고, 파일은 UTF-8로 저장 |
| `gh` 명령이 권한 오류 | 로그인 안 됨 또는 권한 부족 | `gh auth login`, 비공개 저장소는 `repo` 권한 필요 |
| 클라우드 세션이 규칙을 안 따름 | 고른 저장소에 규칙이 없음 | 그 저장소에 `.claude/rules/`와 `CLAUDE.md`가 있는지 확인 |
| 규칙을 고쳤는데 로컬에 반영 안 됨 | 동기화를 안 함 | `git pull` 후 `sync-local.ps1` 다시 실행 |
