<!--
  각 프로젝트 저장소 루트에 CLAUDE.md로 복사해 쓰는 템플릿입니다.
  클라우드 세션은 고른 저장소만 보기 때문에, claude-home의 .claude/rules/에서 필요한 파일을
  이 저장소의 .claude/rules/로 함께 복사합니다(basics, coding, docs, git + 언어별 lang/*.md).
  공통 규칙은 그쪽에서 자동으로 읽히므로 여기에는 이 저장소만의 내용만 적습니다.
  저장소에 AGENTS.md가 있으면 맨 아래 @AGENTS.md 줄을 살려 두세요.
-->

# <저장소 이름>

<이 저장소가 무엇인지 한두 문장>

이 파일은 목차입니다. 자세한 내용은 아래 담당 문서에 있습니다.

## 작업별로 먼저 읽을 문서

| 하려는 일 | 먼저 읽을 문서 |
|---|---|
| 로컬에서 실행하고 코드 바꾸기 | [README.md](README.md)의 시작하기 → <구조·모듈 문서> |
| 설계를 바꾸거나 설계 의도 파악 | [docs/adr/](docs/adr/) |
| 진행 중인 큰 작업 이어서 하기 | [docs/exec-plans/](docs/exec-plans/README.md) |
| 변경 이력 확인 | [CHANGELOG.md](CHANGELOG.md) |
| <이 저장소에 자주 하는 작업> | <담당 문서> |

## 명령어

```bash
<설치>
<실행>
<테스트>
<포맷·린트>
```

## 구조

- <주요 폴더와 역할>

## 이 저장소 규칙

- <공통 규칙과 다른 점, 주의할 점>
- 번역 저장소라면: 번역 원칙과 용어는 [TRANSLATION.md](TRANSLATION.md)를 따릅니다.

<!-- @AGENTS.md -->
