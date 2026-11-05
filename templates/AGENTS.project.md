<!--
  각 프로젝트 저장소 루트에 AGENTS.md로 복사해 쓰는 템플릿입니다(scripts/new_project.py가 채워 줍니다).
  Codex는 이 파일을 직접 읽고, Claude Code는 CLAUDE.md의 @AGENTS.md 줄로 읽습니다.
  위쪽에는 이 저장소만의 안내를 적고, 맨 아래 공통 규칙 부분은 claude-home의 scripts/sync_rules.py가 채웁니다.
  공통 규칙이 약 125줄이라 저장소 안내는 70줄 안쪽으로 씁니다. repo_checks.py가 AGENTS.md 200줄(Claude Code 권장)과
  32KiB(Codex 기본 한도)를 넘으면 알립니다. 자세한 내용은 담당 문서에 두고 여기에는 링크만 둡니다.
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

## 동작 확인

테스트와 별개로, 바꾼 동작을 사용자처럼 실제로 확인하는 방법입니다. 완료 보고에는 여기서 실행한 명령과 결과를 붙입니다.

- <앱·CLI를 띄우는 명령과 열 주소>
- <확인할 화면, 요청, 출력과 기대 결과>

## 구조

- <주요 폴더와 역할>

## 이 저장소 규칙과 확인된 사실

- <공통 규칙과 다른 점, 주의할 점. 확인된 사실은 "이 저장소에서는 ..."으로 쓰고 근거를 붙임>
- 번역 저장소라면: 번역 원칙과 용어는 [TRANSLATION.md](TRANSLATION.md)를 따릅니다.

<!-- claude-home:common-rules:start -->
<!-- claude-home:common-rules:end -->
