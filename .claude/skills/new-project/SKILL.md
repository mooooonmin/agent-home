---
name: new-project
description: claude-home 규칙·검사·문서 틀을 깐 새 프로젝트를 만들고 초기 구축까지 진행
argument-hint: <이름> <java|python|typescript|dart|go> [한 줄 설명]
---

입력: $ARGUMENTS

`$ARGUMENTS`가 비어 있거나 그대로 보이면(Codex 등) 사용자 메시지에서 찾고, 없으면 묻습니다.

claude-home 기준으로 새 프로젝트를 만들고 체계적으로 시작합니다. **로컬 PC에서만** 씁니다. 클라우드 세션은 세션에 넣은 저장소 밖에 새 저장소를 만들지 않으므로, 클라우드에서 실행했다면 멈추고 그렇게 안내합니다. 단계마다 무엇을 했는지 짧게 알리고, 사용자 확인이 필요한 곳에서는 멈춰서 묻습니다.

## 1. 정하기

- 이름, 언어, 한 줄 설명 중 빠진 것이 있으면 먼저 묻습니다.
- 목표가 모호하면 두세 가지만 묻습니다: 누가 쓰는지, 첫 버전에서 꼭 되어야 하는 것 하나, 하지 않을 것.
- 번역 저장소라면 `--translation`을 붙입니다.

## 2. 틀 깔기

스크립트(`scripts/new_project.py`, Python 3.11 이상)는 claude-home 저장소 안에 있습니다. 현재 폴더에 없으면 claude-home 위치를 묻고 그 경로의 스크립트를 씁니다(로컬 PC 기준 보통 `C:\00.PROJECT\claude-home`).

1. claude-home을 최신으로 받습니다. 스크립트는 GitHub이 아니라 이 PC의 claude-home 폴더에서 파일을 복사하기 때문입니다.
   ```bash
   git -C <claude-home 경로> status --short --branch
   ```
   `main`이고 커밋하지 않은 변경이 없으면 받습니다. 다른 브랜치이거나 변경이 있거나 받기에 실패하면, 사용자에게 알리고 그대로 진행할지 묻습니다.
   ```bash
   git -C <claude-home 경로> pull
   ```
2. 미리보기로 만들 파일을 확인합니다. 아무것도 만들지 않습니다.
   ```bash
   python -I scripts/new_project.py --name <이름> --language <언어> --description "<설명>"
   ```
3. 사용자에게 위치(기본: claude-home 옆 폴더, 바꾸려면 `--path`)와 파일 목록을 알리고, 같은 명령에 `--apply`를 붙여 만듭니다. 규칙·스킬·검사·훅 스크립트와 훅 설정도 이때 함께 들어가고 `git init -b main`까지 합니다.
4. 이후 작업은 새 폴더의 절대 경로에서 합니다.

## 3. 뼈대 만들기

언어 공식 도구로 뼈대를 만듭니다. **이미 있는 파일(README.md, .gitignore, 린트 설정)은 덮어쓰지 않습니다.** 도구가 덮어쓰려 하면 임시 폴더에 만든 뒤 없는 파일만 옮기고, 도구가 만든 `.gitignore` 항목은 기존 파일에 합칩니다.

| 언어 | 도구 | 이어서 할 일 |
|---|---|---|
| java | Spring Initializr(start.spring.io, Gradle·Java 17) 또는 `gradle init` | `templates/lint/java/spotless.gradle`을 `build.gradle`에 붙이고 `ArchitectureTest.java`를 테스트 폴더에 넣어 패키지 이름을 맞춤 |
| python | `uv init` 또는 `pyproject.toml` 직접 작성 (`src/` 구조) | 계층이 있으면 `templates/lint/python/importlinter.toml` 적용, 개발 의존성은 `requirements-dev.txt`에 `==`로 고정 |
| typescript | 용도에 맞는 공식 생성기(Vite 등) | `templates/lint/typescript/tsconfig.strict.json` 항목을 `tsconfig.json`에 합치고 ESLint·Prettier 설치 |
| dart | `flutter create --project-name <이름> .` (기존 파일은 덮어쓰지 않음) | 생성된 `analysis_options.yaml`이 우리 것으로 남았는지 확인 |
| go | `go mod init <모듈 경로>` | `cmd/`, `internal/` 구조로 시작 |

파일을 내려받거나 패키지를 설치하기 전에는 무엇을 받는지 알리고 확인을 받습니다.

## 4. 문서 채우기

`docs/exec-plans/active/0001-initial-setup.md`의 단계를 따라가며 체크합니다.

- **ADR**: 기술 선택(언어·프레임워크·저장 방식)을 `docs/adr/0001-<제목>.md`로 씁니다. 템플릿은 `docs/adr/template.md`입니다.
- **README**: 시작하기(설치·실행·테스트 명령)와 구조를 실제 내용으로 채웁니다.
- **AGENTS.md**: 작업별로 먼저 읽을 문서 표, 명령어의 `<설치>`, `<실행>`, 동작 확인 방법, 구조를 채웁니다. 맨 아래 공통 규칙 부분(`claude-home:common-rules` 표시 사이)은 고치지 않습니다. `CLAUDE.md`는 `@AGENTS.md` 줄을 그대로 둡니다.
- 자리표시(`<...>`)가 남지 않게 합니다. 아직 정할 수 없는 것은 실행 계획의 "결정과 남은 문제"로 옮깁니다.

## 5. 첫 기능과 검증

- 핵심 기능 하나를 작게 만들고 테스트를 붙입니다.
- 다음을 모두 로컬에서 돌리고 결과를 실행 계획의 "검증" 표에 적습니다.
  - `python -I scripts/repo_checks.py`
  - AGENTS.md의 포맷·린트·테스트 명령
- 돌리지 못한 검사는 "미확인"으로 남기고 이유를 적습니다.

## 6. 커밋과 GitHub

- 첫 커밋은 `main`에 `chore: 프로젝트 초기 구성`으로 합니다(빈 저장소라 기준 브랜치가 없음). 커밋 본문은 공통 규칙(커밋과 PR)의 양식을 따릅니다.
- GitHub 저장소 생성(공개/비공개)과 푸시는 **사용자에게 확인을 받은 뒤** 합니다.
- 저장소를 만든 직후 병합된 PR의 브랜치가 자동으로 지워지게 설정합니다. 저장소를 만들겠다는 확인에 이 설정도 포함해서 묻습니다.
  ```bash
  gh repo edit <owner>/<이름> --delete-branch-on-merge
  ```
  설정이 바뀌었는지 `gh api repos/<owner>/<이름> --jq .delete_branch_on_merge`로 확인합니다(`true`).
- 푸시한 뒤 CI(`checks`, 언어 워크플로) 결과를 확인하고 실행 계획에 적습니다. 모두 통과하면 계획을 `completed/`로 옮깁니다.

## 끝내며

만든 위치, 통과한 검사, 남은 결정(실행 계획의 남은 문제)을 짧게 보고합니다.
