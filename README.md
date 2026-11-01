# claude-home

내 Claude Code 공통 규칙·명령어·용어집·템플릿을 모아 둔 **비공개** 저장소입니다.
클라우드 세션을 시작할 때 이 저장소를 고르면 PC에서 쓰던 규칙 그대로 작업을 맡길 수 있습니다.

## 구조

```
claude-home/
├─ CLAUDE.md                 # 공통 규칙 (세션마다 자동으로 읽힘)
├─ rules/
│  ├─ translation.md         # 번역 원칙
│  └─ git.md                 # 커밋·PR 규칙
├─ .claude/
│  ├─ settings.json          # 권한 (비밀값 파일 읽기 금지)
│  └─ commands/              # /translate-chapter, /review-translation, /research
├─ glossary/                 # *-ko 저장소에서 모은 분야별 용어집
├─ templates/
│  ├─ CLAUDE.project.md      # 각 프로젝트에 복사할 짧은 CLAUDE.md
│  ├─ pr-body.md
│  └─ translation-repo/      # 새 번역 저장소용 README·NOTICE·TRANSLATION.md
└─ notes/                    # 조사·초안 결과물
```

## 쓰는 법

### 이 저장소에서 바로 맡기기

클라우드 세션을 이 저장소로 열고 명령어를 씁니다.

- `/research <주제>`: 조사해서 `notes/`에 정리
- 번역 저장소 작업은 아래처럼 그 저장소로 세션을 엽니다.

### 다른 프로젝트에서 쓰기

클라우드 세션은 **고른 저장소 하나만** 봅니다. 그래서 프로젝트 저장소에도 규칙이 있어야 합니다.

1. `templates/CLAUDE.project.md`를 프로젝트 루트에 `CLAUDE.md`로 복사하고 채웁니다.
2. 번역 명령어가 필요하면 `.claude/commands/`를 프로젝트의 `.claude/commands/`로 복사합니다.
3. 저장소에 `AGENTS.md`가 있으면 `CLAUDE.md` 맨 아래에 `@AGENTS.md`를 넣어 같은 규칙을 함께 씁니다.

이 저장소가 규칙의 **원본**입니다. 규칙을 고칠 땐 여기서 고친 뒤 프로젝트로 복사합니다.

### 로컬 PC에서도 같은 규칙 쓰기

이 저장소의 `CLAUDE.md`를 `~/.claude/CLAUDE.md`에서 불러오면 모든 로컬 세션에 적용됩니다.

```
@C:/00.PROJECT/claude-home/CLAUDE.md
```

## 비밀값

API 키·토큰은 이 저장소에 넣지 않습니다. 클라우드 세션의 **환경 설정**에 환경 변수로 등록합니다. `.env`는 `.gitignore`에 들어 있습니다.
