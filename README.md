# claude-home

Claude Code와 Codex가 함께 쓰는 공통 규칙·스킬·용어집·템플릿을 모아 둔 **비공개** 저장소입니다.
공통 규칙은 `AGENTS.md` 하나에 있고, Codex는 이 파일을 직접, Claude Code는 `CLAUDE.md`의 `@AGENTS.md` 줄로 읽습니다.
클라우드 세션을 시작할 때 이 저장소를 고르면 PC에서 쓰던 규칙 그대로 작업을 맡길 수 있습니다.

> [!TIP]
> 처음이거나 새 PC라면 [초기 설정](docs/setup.md)부터 따라 하세요. 필요한 도구, 받는 위치, 로컬 동기화, 클라우드 설정, 문제 해결이 순서대로 있습니다.

## 구조

```
claude-home/
├─ AGENTS.md                     # 이 저장소 안내 + 공통 규칙(소통·작업 방식, 코딩, 문서, 커밋과 PR)의 원본
├─ CLAUDE.md                     # @AGENTS.md (Claude Code가 AGENTS.md를 읽게 함)
├─ .agents/skills/               # 스킬 원본: new-project, research, update-docs, translate-chapter, review-translation (Codex)
├─ .github/                      # 이 저장소 CI, PR 템플릿(새 프로젝트에도 복사)
├─ .claude/
│  ├─ settings.json              # 권한 (비밀값 파일 읽기 금지)
│  ├─ skills/                    # .agents/skills와 같은 사본 (Claude Code)
│  └─ rules/                     # 해당 파일을 다룰 때 읽히는 규칙 (Claude Code는 자동, Codex는 AGENTS.md의 표를 보고 읽음)
│     ├─ translation.md          # 번역 (.md, .ipynb)
│     └─ lang/                   # java, python, typescript, dart, go
├─ docs/setup.md                 # 초기 설정 안내
├─ glossary/                     # *-ko 저장소에서 모은 분야별 용어집
├─ templates/
│  ├─ AGENTS.project.md          # 각 프로젝트의 AGENTS.md 저장소 안내 부분
│  ├─ CLAUDE.project.md          # 각 프로젝트의 CLAUDE.md (@AGENTS.md)
│  ├─ lint/                      # 언어별 린트·포맷·계층 검사 설정, .editorconfig, .gitattributes, .gitignore
│  ├─ docs/                      # README, 폴더 README, CHANGELOG, ADR, 실행 계획·개선 목록 템플릿
│  ├─ ci/                        # 저장소 검사 스크립트와 테스트, GitHub Actions (공통 + lang/ 언어별 빌드·테스트)
│  └─ translation-repo/          # 새 번역 저장소용 README·NOTICE·TRANSLATION.md
├─ scripts/
│  ├─ new-project.ps1            # 규칙·검사·문서 틀을 깐 새 프로젝트 만들기
│  ├─ sync_rules.py              # 공통 규칙·스킬·검사 도구를 프로젝트, 사용자 설정, .claude/skills로 복사
│  └─ test_sync_rules.py         # sync_rules.py 테스트
└─ notes/                        # 조사·초안 결과물
```

## 쓰는 법

### 이 저장소에서 바로 맡기기

클라우드 세션을 이 저장소로 열고 스킬을 씁니다. 연결과 환경 설정은 [초기 설정의 클라우드 세션 설정](docs/setup.md#5-클라우드-세션-설정)을 봅니다.

- `/research <주제>`: 조사해서 `notes/`에 정리
- 번역·코딩 작업은 아래처럼 그 저장소로 세션을 엽니다.

### 새 프로젝트 시작하기

**로컬 PC에서** 이 저장소를 열고 `new-project` 스킬로 시작합니다. 클라우드에는 `pwsh`가 없어서 쓸 수 없습니다.

먼저 최신 규칙을 받습니다. 스크립트는 GitHub이 아니라 이 PC에 받아 둔 claude-home 폴더의 파일을 복사합니다.

```bash
git -C C:/00.PROJECT/claude-home pull
```

Claude Code에서는 다음처럼 부릅니다. Codex에서는 `$new-project`로 스킬을 고르고 같은 내용을 적습니다.

```
/new-project my-app python 할 일 목록 CLI
```

다음 순서로 진행합니다.

1. `scripts/new-project.ps1`로 새 폴더에 린트 설정, `.gitignore`, CI(공통 + 언어별), README·AGENTS.md·CLAUDE.md·CHANGELOG, ADR 템플릿, 첫 실행 계획을 깔고 `git init` 합니다. 마지막에 `scripts/sync_rules.py`가 공통 규칙, 언어 규칙, 스킬, 검사 스크립트를 넣습니다.
2. 언어 공식 도구(Spring Initializr, `uv init`, Vite, `flutter create`, `go mod init`)로 뼈대를 만듭니다. 이미 깐 파일은 덮어쓰지 않습니다.
3. 첫 실행 계획(`docs/exec-plans/active/0001-initial-setup.md`)을 따라 ADR, README, AGENTS.md를 채우고 첫 기능과 테스트를 만듭니다.
4. 로컬 검사가 모두 통과하면 첫 커밋을 하고, 확인을 받은 뒤 GitHub에 올려 CI를 확인합니다. GitHub 저장소에는 병합된 PR의 브랜치를 자동으로 지우는 설정을 켭니다.

스크립트만 따로 쓸 수도 있습니다. `-WhatIf`를 붙이면 만들 파일만 보여 줍니다.

```bash
pwsh -File scripts/new-project.ps1 -Name my-app -Language python -Description "할 일 목록 CLI" -WhatIf
```

새 프로젝트의 규칙은 만들 때 복사한 **사본**입니다. 프로젝트에서 고친 규칙은 그 프로젝트에만 적용되고 claude-home은 바뀌지 않습니다. 원본을 고친 뒤 반영하는 법과 주의점은 [초기 설정의 규칙을 고친 뒤](docs/setup.md#규칙을-고친-뒤)를 봅니다.

### 기존 프로젝트에 적용하기

클라우드 세션에는 **세션에 넣은 저장소의 파일만** 있고 내 PC의 `~/.claude/`, `~/.codex/`는 따라가지 않습니다. 그래서 프로젝트 저장소에도 규칙이 있어야 합니다.

1. 미리보기로 바뀔 파일을 확인합니다. 공통 규칙은 프로젝트 `AGENTS.md`의 `claude-home:common-rules` 표시 사이에만 들어가고(없으면 맨 아래에 붙음), 언어 규칙·`update-docs` 스킬·검사 스크립트가 함께 들어갑니다.
   ```bash
   python -I scripts/sync_rules.py --target ../my-app --lang python
   ```
2. 문제없으면 `--apply`를 붙여 반영합니다. 번역 저장소라면 `--translation`도 붙입니다.
   ```bash
   python -I scripts/sync_rules.py --target ../my-app --lang python --apply
   ```
3. 프로젝트에 원래 `CLAUDE.md`가 있었다면 맨 위에 `@AGENTS.md` 줄을 넣습니다. 도구가 "확인 필요"로 알려 줍니다.
4. `AGENTS.md` 위쪽(표시 밖)에 저장소 안내를 채웁니다. 형식은 `templates/AGENTS.project.md`를 봅니다.
5. 언어에 맞는 `templates/lint/` 설정과 `templates/ci/`의 GitHub Actions를 넣습니다.

이 저장소가 규칙의 **원본**입니다. 규칙을 고칠 땐 여기서 고친 뒤 같은 명령으로 프로젝트에 다시 반영합니다.

### 로컬 PC에서도 같은 규칙 쓰기

공통 규칙과 스킬을 사용자 설정(`~/.claude/`, `~/.codex/AGENTS.md`, `~/.agents/skills/`)에 넣으면 이 PC의 모든 프로젝트에서 Claude Code와 Codex가 같은 규칙을 따릅니다. 자세한 내용은 [초기 설정](docs/setup.md#3-로컬-pc에-규칙-적용)을 봅니다.

```bash
python -I scripts/sync_rules.py --user --apply
```

## 비밀값

API 키·토큰은 이 저장소에 넣지 않습니다. 클라우드에서는 환경 설정의 **Network secrets**에 넣습니다(환경 변수는 그 환경을 쓰는 사람이 모두 볼 수 있음). `.env`는 `.gitignore`에 들어 있습니다.
