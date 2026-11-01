# claude-home

내 Claude Code 공통 규칙·명령어·용어집·템플릿을 모아 둔 **비공개** 저장소입니다.
클라우드 세션을 시작할 때 이 저장소를 고르면 PC에서 쓰던 규칙 그대로 작업을 맡길 수 있습니다.

## 구조

```
claude-home/
├─ CLAUDE.md                     # 이 저장소 안내 (규칙 목록)
├─ .claude/
│  ├─ settings.json              # 권한 (비밀값 파일 읽기 금지)
│  ├─ rules/                     # 자동으로 읽히는 규칙
│  │  ├─ basics.md               # 소통, 작업 방식, 비밀값
│  │  ├─ coding.md               # 코딩 스타일, 설계 원칙
│  │  ├─ docs.md                 # 문서 최신화 규칙
│  │  ├─ git.md                  # 커밋·PR
│  │  ├─ translation.md          # 번역 (.md, .ipynb 작업 때만)
│  │  └─ lang/                   # java, python, typescript, dart, go (해당 언어 작업 때만)
│  └─ commands/                  # /new-project, /update-docs, /research, /translate-chapter, /review-translation
├─ glossary/                     # *-ko 저장소에서 모은 분야별 용어집
├─ templates/
│  ├─ CLAUDE.project.md          # 각 프로젝트에 복사할 짧은 CLAUDE.md
│  ├─ pr-body.md
│  ├─ lint/                      # 언어별 린트·포맷·계층 검사 설정, .editorconfig, .gitattributes, .gitignore
│  ├─ docs/                      # README, 폴더 README, CHANGELOG, ADR, 실행 계획·개선 목록 템플릿
│  ├─ ci/                        # 저장소 검사 스크립트와 테스트, GitHub Actions (공통 + lang/ 언어별 빌드·테스트)
│  └─ translation-repo/          # 새 번역 저장소용 README·NOTICE·TRANSLATION.md
├─ scripts/
│  ├─ new-project.ps1            # 규칙·검사·문서 틀을 깐 새 프로젝트 만들기
│  └─ sync-local.ps1             # 규칙·명령어를 ~/.claude/로 복사
└─ notes/                        # 조사·초안 결과물
```

## 쓰는 법

### 이 저장소에서 바로 맡기기

클라우드 세션을 이 저장소로 열고 명령어를 씁니다.

- `/research <주제>`: 조사해서 `notes/`에 정리
- 번역·코딩 작업은 아래처럼 그 저장소로 세션을 엽니다.

### 새 프로젝트 시작하기

이 저장소에서 Claude Code를 열고 명령어 하나로 시작합니다.

```
/new-project my-app python 할 일 목록 CLI
```

Claude가 다음 순서로 진행합니다.

1. `scripts/new-project.ps1`로 새 폴더에 규칙, 린트 설정, `.gitignore`, 검사 스크립트, CI(공통 + 언어별), README·CLAUDE.md·CHANGELOG, ADR 템플릿, 첫 실행 계획을 깔고 `git init` 합니다.
2. 언어 공식 도구(Spring Initializr, `uv init`, Vite, `flutter create`, `go mod init`)로 뼈대를 만듭니다. 이미 깐 파일은 덮어쓰지 않습니다.
3. 첫 실행 계획(`docs/exec-plans/active/0001-initial-setup.md`)을 따라 ADR, README, CLAUDE.md를 채우고 첫 기능과 테스트를 만듭니다.
4. 로컬 검사가 모두 통과하면 첫 커밋을 하고, 확인을 받은 뒤 GitHub에 올려 CI를 확인합니다.

스크립트만 따로 쓸 수도 있습니다. `-WhatIf`를 붙이면 만들 파일만 보여 줍니다.

```bash
pwsh -File scripts/new-project.ps1 -Name my-app -Language python -Description "할 일 목록 CLI" -WhatIf
```

### 기존 프로젝트에 적용하기

클라우드 세션은 **고른 저장소 하나만** 봅니다. 그래서 프로젝트 저장소에도 규칙이 있어야 합니다.

1. `.claude/rules/`에서 필요한 파일을 프로젝트의 `.claude/rules/`로 복사합니다. 보통 `basics.md`, `coding.md`, `docs.md`, `git.md`와 그 프로젝트 언어의 `lang/*.md`면 됩니다.
2. `templates/CLAUDE.project.md`를 프로젝트 루트에 `CLAUDE.md`로 복사하고 빌드·테스트 명령을 채웁니다.
3. 언어에 맞는 `templates/lint/` 설정과 `templates/ci/`의 저장소 검사를 넣습니다.
4. 필요한 명령어(`/update-docs`, `/translate-chapter` 등)를 프로젝트의 `.claude/commands/`로 복사합니다.
5. 저장소에 `AGENTS.md`가 있으면 `CLAUDE.md` 맨 아래에 `@AGENTS.md`를 넣어 같은 규칙을 함께 씁니다.

이 저장소가 규칙의 **원본**입니다. 규칙을 고칠 땐 여기서 고친 뒤 프로젝트로 복사합니다.

### 로컬 PC에서도 같은 규칙 쓰기

`~/.claude/rules/`와 `~/.claude/commands/`에 넣은 파일은 이 PC의 모든 프로젝트에 적용됩니다. 규칙을 고친 뒤 다음을 실행합니다.

```bash
pwsh -File scripts/sync-local.ps1
```

## 비밀값

API 키·토큰은 이 저장소에 넣지 않습니다. 클라우드 세션의 **환경 설정**에 환경 변수로 등록합니다. `.env`는 `.gitignore`에 들어 있습니다.
