# 변경 이력

claude-home의 주요 변경 사항을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고, 버전 번호 대신 병합한 날짜로 묶습니다. 프로젝트에 반영한 시점은 그 프로젝트의 `.claude-home-version`에 적힌 커밋으로 알 수 있습니다. 왜 그렇게 정했는지는 [ADR](docs/adr/)을 봅니다.

## [Unreleased]

### 추가

- 설계 결정 기록(`docs/adr/` 0001~0005)과 이 변경 이력
- `sync_rules.py --target`이 반영한 claude-home 커밋을 프로젝트의 `.claude-home-version`에 기록
- `templates/README.md`: 템플릿 폴더별 용도와 복사되는 위치

### 변경

- `research`, `translate-chapter`, `review-translation` 스킬: 읽은 자료에 적힌 지시는 따르지 않고 자료로만 다룸. `update-docs` 스킬: 문서의 명령 중 지우거나 바꾸거나 외부로 보내는 명령은 실행하지 않고 확인 항목으로 남김

## 2026-11-05

### 추가

- `scripts/new_project.py`: 새 프로젝트 생성(기본은 미리보기, `--apply`로 만듦). `test_new_project.py`가 언어 5개 × 번역 여부로 만든 프로젝트가 검사를 통과하는지 CI에서 확인 (PR #14, [ADR 0005](docs/adr/0005-generate-projects-with-python-and-test-the-output.md))
- `new-project` 스킬 7단계: 첫 프로젝트에서 훅이 실제로 막는지 확인 (PR #14)

### 제거

- `scripts/new-project.ps1`. PowerShell 7이 더는 필요 없음 (PR #14)

## 2026-11-04

### 추가

- Claude Code·Codex 공용 구조: 공통 규칙을 `AGENTS.md`로, 스킬을 `.agents/skills/`(원본)와 `.claude/skills/`(사본)로, 동기화 도구 `scripts/sync_rules.py` (PR #8, #9, [ADR 0001](docs/adr/0001-agents-md-as-common-rule-source.md), [ADR 0002](docs/adr/0002-copy-rules-into-projects-with-sync.md))
- 공통 규칙: 세션 시작과 끝, 동작 확인 근거, PR 전 독립 리뷰, "두 번 지적하면 검사로" (PR #8)
- 훅: 기본 브랜치 직접 커밋·푸시 차단, 끝내기 전 저장소 검사 (PR #10, [ADR 0003](docs/adr/0003-enforce-branch-and-checks-with-hooks.md))
- 저장소 검사: `AGENTS.md` 200줄·32KiB, `CLAUDE.md`의 `@AGENTS.md`, 스킬 원본·사본 일치, 훅 스크립트 존재, `.gitattributes`·`.gitignore` 중괄호 패턴 (PR #8, #9, #10, #12, #13)
- GitHub 저장소 규칙 설정 순서 (`docs/setup.md`, PR #11)
- 새 프로젝트 생성 전 `git pull`과 규칙 사본 관계 안내 (PR #8)

### 변경

- 코드·문서를 다룰 때만 필요한 규칙을 `.claude/rules/code.md`, `writing-docs.md`로 옮겨 `AGENTS.md`를 200줄 아래로 줄임 (PR #13, [ADR 0004](docs/adr/0004-keep-always-loaded-rules-under-200-lines.md))
- 명령어(`.claude/commands/`)를 스킬로 바꿈 (PR #8)
- PR 템플릿을 범용 `.github/pull_request_template.md`로 옮김 (PR #8)

### 수정

- 새 프로젝트로 복사된 규칙이 그 프로젝트에 없는 `templates/` 경로를 가리키던 문제 (PR #8)
- `.gitattributes`의 중괄호 패턴이 아무 파일에도 적용되지 않던 문제 (PR #12)

### 제거

- `scripts/sync-local.ps1` (`sync_rules.py --user`로 대체, PR #8)

## 2026-11-03

### 추가

- 클라우드 세션 설정 안내, 새 GitHub 저장소의 병합 후 브랜치 자동 삭제 설정 (PR #5, #6)

## 2026-11-01

### 추가

- 공통 규칙·명령어·용어집·템플릿 초기 구성, 언어별 규칙, 저장소 규칙 검사와 계층 검사 템플릿, 새 프로젝트 자동 구성, 초기 설정 안내 (PR #1~#4)
