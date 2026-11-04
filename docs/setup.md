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
| PowerShell 7 | `scripts/new-project.ps1` 실행 | `pwsh --version` | `winget install Microsoft.PowerShell` |
| Python 3.11 이상 | 규칙 동기화(`sync_rules.py`), 저장소 검사 | `python --version` | `winget install Python.Python.3.12` |
| Claude Code | 규칙과 스킬 사용 | 데스크톱 앱 또는 `claude --version` | [Claude Code 문서](https://code.claude.com/docs) |
| Codex (함께 쓸 때) | 규칙과 스킬 사용 | `codex --version` | Codex 공식 안내 |

Windows에 기본으로 있는 PowerShell 5(`powershell`)가 아니라 **PowerShell 7(`pwsh`)** 이 필요합니다.

설치 후 GitHub에 로그인합니다.

```bash
gh auth login
```

```bash
gh auth status
```

## 2. 저장소 받기

다른 프로젝트들과 **같은 상위 폴더**에 받습니다. `new-project` 스킬은 claude-home 옆에 새 프로젝트를 만들기 때문입니다.

```bash
gh repo clone mooooonmin/claude-home C:/00.PROJECT/claude-home
```

## 3. 로컬 PC에 규칙 적용

공통 규칙과 스킬을 사용자 설정에 넣으면 이 PC의 **모든 프로젝트**에서 Claude Code와 Codex가 같은 규칙을 따릅니다. 먼저 미리보기로 바뀔 파일을 확인합니다.

```bash
python -I C:/00.PROJECT/claude-home/scripts/sync_rules.py --user
```

문제없으면 실제로 반영합니다.

```bash
python -I C:/00.PROJECT/claude-home/scripts/sync_rules.py --user --apply
```

| 넣는 것 | 위치 | 효과 |
|---|---|---|
| 공통 규칙 (`AGENTS.md`의 표시 사이) | `~/.claude/rules/claude-home.md` | Claude Code: 모든 프로젝트에 적용 |
| 같은 공통 규칙 | `~/.codex/AGENTS.md`의 같은 표시 사이 | Codex: 모든 프로젝트에 적용. 표시 밖에 적어 둔 내 지시는 그대로 둠 |
| `.claude/rules/lang/`, `translation.md` | `~/.claude/rules/` | Claude Code는 해당 파일을 다룰 때 자동으로, Codex는 공통 규칙의 표를 보고 읽음 |
| `.agents/skills/` | `~/.agents/skills/`, `~/.claude/skills/` | 어느 프로젝트에서나 `new-project`, `update-docs` 등을 쓸 수 있음 |

- 같은 이름의 파일은 덮어씁니다. 예전 방식의 사본(`~/.claude/rules/basics.md` 등 4개, `~/.claude/commands/`의 같은 이름 명령)은 claude-home에 있던 내용 그대로일 때만 지웁니다. 고쳤거나 이름만 같은 내 파일은 남기고 "확인 필요"로 알려 줍니다. 그 밖의 파일은 건드리지 않습니다.
- `CLAUDE_CONFIG_DIR`, `CODEX_HOME` 환경 변수를 쓰고 있으면 그 폴더에 넣습니다.
- claude-home이나 claude-home으로 만든 프로젝트에서는 같은 공통 규칙(약 17KB)이 두 번(사용자 설정 + 저장소) 읽혀 그만큼 컨텍스트를 더 씁니다. 내용이 같아 서로 부딪히지는 않습니다. claude-home으로 만든 프로젝트에서만 일한다면 `--user`는 하지 않아도 됩니다(스킬도 프로젝트에 들어 있음).
- 번역 규칙은 `.md`, `.ipynb` 파일을 다룰 때만 읽히고, 저장소에 `TRANSLATION.md`가 있으면 그쪽이 우선합니다.

## 4. 설정 확인

모두 통과하면 설정이 끝난 것입니다.

| 확인 | 명령·방법 | 기대 결과 |
|---|---|---|
| 규칙 복사 | `ls ~/.claude/rules ~/.claude/skills ~/.agents/skills` | `claude-home.md`, `lang/`, `new-project/` 등이 보임 |
| Codex 규칙 | `~/.codex/AGENTS.md` 열기 | `claude-home:common-rules` 표시 사이에 공통 규칙이 있음 |
| 검사·동기화 도구 | claude-home에서 `python -I -m unittest discover -s templates/ci -p "test_*.py"`와 `python -I -m unittest discover -s scripts -p "test_*.py"` | 둘 다 `OK` |
| 저장소 검사 | claude-home에서 `python -I templates/ci/repo_checks.py --docs-exclude templates` | `문제 0개` |
| Codex 훅 승인 | claude-home(과 각 프로젝트)에서 Codex를 열고 `/hooks` | 저장소 훅 2개를 승인함 ([훅](#훅)) |
| 새 프로젝트 미리보기 | claude-home에서 `pwsh -File scripts/new-project.ps1 -Name test-app -Language python -WhatIf` | 만들 파일 목록만 나오고 폴더는 생기지 않음 |
| 규칙 적용 | 아무 프로젝트에서 Claude Code와 Codex를 각각 열고 "지금 적용된 규칙 파일 목록 알려줘"라고 묻기 | Claude Code는 `~/.claude/rules/`, Codex는 `~/.codex/AGENTS.md`가 언급됨 |

## 5. 클라우드 세션 설정

클라우드 세션은 Anthropic의 가상 머신(Ubuntu)에서 돌아서 내 PC를 꺼도 계속 작업합니다. 세션에는 **세션에 넣은 저장소의 파일만** 있고, 내 PC의 `~/.claude/` 설정은 따라가지 않습니다. 그래서 규칙이 저장소 안에 있어야 합니다.

공식 안내: [Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web), [클라우드 환경](https://code.claude.com/docs/en/cloud-environments). 화면 이름은 바뀔 수 있으니 막히면 이 문서를 확인합니다.

### GitHub 연결 (처음 한 번)

claude-home은 **비공개 저장소**라서 아래 둘 중 하나가 필요합니다. 연결하지 않으면 공개 저장소만 열 수 있습니다.

- **브라우저**: [claude.ai/code](https://claude.ai/code)에 로그인해 GitHub 권한을 승인하고, [Claude GitHub App](https://github.com/apps/claude/installations/new)을 설치하면서 접근할 저장소에 `claude-home`(과 클라우드에서 쓸 프로젝트)을 넣습니다. PR Auto-fix도 이 앱이 있어야 동작합니다.
- **터미널**: `gh auth login`이 된 상태에서 Claude Code를 열고 `/login` → `/web-setup`을 실행합니다. `gh`의 권한으로 비공개 저장소에 접근합니다.

### 환경 (처음 한 번)

입력창 아래 **환경 선택**에서 고릅니다. claude-home 작업은 **기본 환경 그대로** 쓰면 됩니다.

| 항목 | claude-home 설정 | 설명 |
|---|---|---|
| Network access | Trusted (기본값) | GitHub, PyPI, npm, Maven 같은 패키지 저장소에 접근 가능 |
| Setup script | 없음 | Python(pytest, ruff 포함), Node, Java 21, Go, `gh`가 미리 설치되어 있음 |
| Environment variables | 없음 | 그 환경을 쓰는 사람이 모두 볼 수 있으므로 API 키는 넣지 않음 |
| Network secrets | 필요할 때만 | API 키는 여기에 넣습니다. 지정한 호스트로 가는 요청에만 붙습니다 |

Flutter/Dart, PowerShell(`pwsh`)은 **미리 설치되어 있지 않습니다**. Flutter 프로젝트를 클라우드에서 다루려면 그 프로젝트용 환경을 새로 만들고 Setup script에 설치 명령을 넣습니다.

### 세션 시작

입력창 아래 **저장소 선택**에서 저장소와 브랜치(`main`)를 고르고 할 일을 적습니다. 주소로 바로 열 수도 있습니다.

```
https://claude.ai/code?repositories=mooooonmin/claude-home&prompt=/research%20조사할%20주제
```

| 하려는 일 | 고를 저장소 |
|---|---|
| 조사·메모 (`/research`, 결과는 `notes/`) | `claude-home` |
| 규칙·템플릿 고치기, `/update-docs` | `claude-home` |
| 특정 프로젝트 작업 | 그 프로젝트 저장소. 공통 규칙이 들어간 `AGENTS.md`와 `@AGENTS.md` 줄이 있는 `CLAUDE.md`가 있어야 규칙이 적용됩니다(`new-project`로 만든 프로젝트에는 이미 있음) |

저장소를 여러 개 함께 넣을 수도 있지만, 그때는 각 저장소의 `.claude/settings.json` 권한 규칙과 훅이 적용되지 않습니다. 보통은 저장소 하나로 엽니다.

### 클라우드에서 적용되는 것

| 적용됨 | 적용 안 됨 |
|---|---|
| 저장소의 `CLAUDE.md`와 그 안의 `@AGENTS.md`, `.claude/rules/` (언어별 규칙) | 내 PC의 `~/.claude/`, `~/.codex/` (규칙, 스킬, 설정) |
| `.claude/skills/` (`/research`, `/update-docs` 등) | `.claude/settings.local.json` |
| `.claude/settings.json`의 권한 규칙과 훅 (저장소 하나일 때) | 플러그인, 내 PC에 추가한 MCP 서버 |

### 클라우드에서 하지 않는 것

- **`new-project`**: `pwsh`가 없고, 세션은 넣은 저장소 밖에 새 저장소를 만들지 않습니다. 새 프로젝트는 로컬에서 만듭니다.
- **`sync_rules.py --user`**: 내 PC의 사용자 설정을 위한 명령이라 클라우드와 상관없습니다.

### 결과 받기

1. 작업이 끝나면 Claude가 작업 브랜치를 GitHub에 올립니다.
2. **Changes** 카드에서 변경 내용을 보고 **Create PR**로 PR을 만듭니다.
3. PR은 직접 확인하고 병합합니다([커밋과 PR 규칙](../AGENTS.md#커밋과-pr-규칙)).
4. 클라우드는 브랜치를 지울 수 없습니다. 병합 후 GitHub에서 지우거나, 저장소 설정의 "Automatically delete head branches"를 켭니다.

로컬과 오가기:

- 클라우드 세션을 내 PC 터미널로 가져오기: 그 저장소 폴더에서 `claude --teleport` (작업 트리가 깨끗해야 함)
- 로컬에서 클라우드로 일 보내기: `claude --cloud "할 일"` (현재 브랜치 기준이므로 먼저 푸시)

### 사용량

- 클라우드 세션은 요금제 사용량에서 차감되고, 가상 머신 비용은 따로 없습니다.
- 세션 여러 개를 동시에 돌리면 사용량 한도를 함께 씁니다.
- 크레딧과 사용량은 Claude 설정의 사용량 화면에서 확인합니다.

## 훅

글로 된 규칙 중 꼭 지켜야 할 두 가지를 Claude Code와 Codex가 같은 스크립트(`templates/ci/agent_hooks.py`, 프로젝트에서는 `scripts/agent_hooks.py`)로 강제합니다.

| 훅 | 언제 | 하는 일 |
|---|---|---|
| `pre-bash` | 셸 명령을 실행하기 전 | `main`·`master`에 바로 커밋하거나 그쪽으로 푸시하는 명령을 막고 이유를 알려 줌. 커밋이 없는 새 저장소의 첫 커밋과, 원격에 아직 그 브랜치가 없는 첫 푸시(`new-project`의 첫 업로드)는 허용 |
| `stop` | 응답을 끝내기 전 | 바뀐 파일이 있으면 저장소 검사(`repo_checks.py`)를 돌리고, 실패하면 끝내지 않고 고치게 함. 한 번 막은 뒤에는 다시 막지 않음 |

| 도구 | 설정 파일 | 처음 할 일 |
|---|---|---|
| Claude Code | `.claude/settings.json`의 `hooks` | 없음. 저장소를 열면 적용됨 |
| Codex | `.codex/hooks.json` | 저장소마다 Codex에서 `/hooks`를 열어 두 훅을 승인. Codex는 승인하지 않았거나 내용이 바뀐 저장소 훅을 실행하지 않음(Codex 소스 `codex-rs/hooks/src/engine/discovery.rs` 기준, 화면 흐름은 미확인) |

- 두 훅 모두 `python`을 부릅니다. Windows에서는 `python`이 PATH에 있어야 합니다.
- 훅 스크립트 파일이 없으면 `python`이 종료 코드 2로 끝나고, 두 도구 모두 이것을 "막음"으로 처리해 셸 명령이 모두 막힙니다. `repo_checks.py`가 설정이 가리키는 스크립트가 있는지 검사합니다.
- 꼭 기본 브랜치에 바로 올려야 하면 에이전트에게 맡기지 말고 직접 실행합니다.

## 규칙을 고친 뒤

claude-home이 규칙의 원본입니다. 규칙은 항상 여기서 고치고 다른 곳으로 퍼뜨립니다.

1. claude-home에서 작업 브랜치를 만들어 고치고, PR로 `main`에 병합합니다.
2. 이 PC에 반영합니다.
   ```bash
   git -C C:/00.PROJECT/claude-home pull
   ```
   ```bash
   python -I C:/00.PROJECT/claude-home/scripts/sync_rules.py --user --apply
   ```
3. 프로젝트에도 반영합니다. 자동으로 따라가지 않으므로, 프로젝트마다 미리보기로 확인한 뒤 `--apply`로 반영하고 그 저장소에서 커밋합니다.
   ```bash
   python -I C:/00.PROJECT/claude-home/scripts/sync_rules.py --target C:/00.PROJECT/my-app
   ```
4. 다른 PC에서는 2번만 하면 됩니다.

### 원본과 사본

- 프로젝트 `AGENTS.md`의 공통 규칙 부분, `.claude/rules/`, 스킬은 `new-project`나 `sync_rules.py`로 넣은 **사본**이고, 원본과 연결되어 있지 않습니다.
  - claude-home을 고쳐도 프로젝트는 그대로입니다(위 3번).
  - 프로젝트에서 고친 규칙은 그 프로젝트에만 적용되고 claude-home은 바뀌지 않습니다. 모든 프로젝트에 적용할 규칙은 claude-home에서 고칩니다.
  - 프로젝트만의 규칙은 `AGENTS.md`의 공통 규칙 표시 **밖**(위쪽 저장소 안내)에 적습니다. 표시 사이는 다음 동기화 때 원본으로 덮어씁니다.
- 새 프로젝트를 만들기 전에는 위 2번의 `git pull`을 먼저 합니다. `scripts/new-project.ps1`은 GitHub이 아니라 이 PC의 claude-home 폴더에서 파일을 복사합니다.
- 로컬 PC에서는 프로젝트의 규칙과 사용자 설정(`~/.claude/rules/`, `~/.codex/AGENTS.md`)의 원본이 **함께** 읽힙니다. 어느 쪽도 다른 쪽을 덮어쓰지 않고, 둘이 충돌하면 Claude가 어느 쪽을 따를지 정해지지 않습니다([공식 문서: User-level rules](https://code.claude.com/docs/en/memory)). 그래서 프로젝트 규칙은 원본에 **덧붙이는** 내용으로 쓰고, 원본과 반대되는 규칙이 필요하면 claude-home을 고칠지 먼저 검토합니다.
- 클라우드 세션에서는 [세션에 넣은 저장소의 규칙만](#클라우드에서-적용되는-것) 읽힙니다.

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `pwsh`를 찾을 수 없음 | PowerShell 7이 없음 | `winget install Microsoft.PowerShell` 후 터미널을 새로 엶 |
| 스크립트 실행이 막힘 (`running scripts is disabled`) | 실행 정책 | `pwsh -ExecutionPolicy Bypass -File <스크립트>`로 그 실행만 허용 |
| `git init`이 실패했다는 경고 (`Filename too long`) | Windows 경로 길이 제한(260자) | 더 짧은 경로에 만들거나 `git config --global core.longpaths true` |
| 한글이 깨져 보임 | 터미널 인코딩 | PowerShell 7을 쓰고, 파일은 UTF-8로 저장 |
| `gh` 명령이 권한 오류 | 로그인 안 됨 또는 권한 부족 | `gh auth login`, 비공개 저장소는 `repo` 권한 필요 |
| 클라우드 세션이 규칙을 안 따름 | 고른 저장소에 규칙이 없거나 `CLAUDE.md`가 `AGENTS.md`를 가져오지 않음 | 그 저장소 `AGENTS.md`에 공통 규칙 표시가 있고 `CLAUDE.md`에 `@AGENTS.md` 줄이 있는지 확인 (`repo_checks.py`가 뒤쪽을 검사) |
| Codex가 규칙 뒷부분을 모름 | `AGENTS.md`가 Codex 기본 한도(32KiB)를 넘어 잘림 | `repo_checks.py`로 크기를 확인하고 자세한 내용을 담당 문서로 옮김 |
| 클라우드 저장소 목록에 `claude-home`이 없음 | 비공개 저장소 접근 권한 없음 | Claude GitHub App 설치 시 그 저장소를 포함하거나 `/web-setup` |
| 클라우드에서 `flutter`나 `pwsh`를 찾을 수 없음 | 미리 설치되어 있지 않음 | 그 프로젝트용 환경의 Setup script에 설치 명령 추가 |
| 에이전트가 모든 셸 명령을 못 함 (`can't open file … agent_hooks.py`) | 훅 설정은 있는데 훅 스크립트가 없음 | claude-home에서 `sync_rules.py --target <프로젝트> --apply`로 넣거나, 훅 설정을 지움 |
| Codex에서 훅이 돌지 않음 | 저장소 훅을 아직 승인하지 않았거나 훅 내용이 바뀜 | Codex에서 `/hooks`로 승인 |
| 규칙을 고쳤는데 로컬에 반영 안 됨 | 동기화를 안 함 | `git pull` 후 `sync_rules.py --user --apply` 다시 실행 |
| 스킬 사본이 원본과 다르다는 검사 오류 | `.agents/skills/`만 고치고 `.claude/skills/`에 복사하지 않음 | claude-home에서는 `sync_rules.py --mirror --apply`, 프로젝트에서는 원본 파일을 그대로 복사 |
