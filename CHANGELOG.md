# 변경 이력

agent-home(예전 이름 claude-home)의 주요 변경 사항을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고, 버전 번호 대신 병합한 날짜로 묶습니다. 프로젝트에 반영한 시점은 그 프로젝트의 `.agent-home-version`(예전 `.claude-home-version`)에 적힌 커밋으로 알 수 있습니다. 왜 그렇게 정했는지는 [ADR](docs/adr/)을 봅니다.

## [Unreleased]

### 추가

- `repo_checks.py`: 커밋 제목이 `type(scope): 설명` 형식인지 검사. 기본은 아직 올리지 않은 커밋, CI는 PR의 커밋 ([ADR 0006](docs/adr/0006-check-commit-titles-instead-of-long-commit-rules.md))
- 셸 명령 전 훅: 명령에 적힌 커밋 제목(`git commit -m "..."`)과 `git push`로 올릴 커밋의 제목을 검사
- `test_new_project.py`: 새 프로젝트 `AGENTS.md`가 180줄을 넘으면 실패 (저장소 안내를 채울 여유 20줄)

### 변경

- 저장소 이름을 claude-home에서 agent-home으로 바꿈. 공통 규칙 표시는 `agent-home:common-rules`, 버전 파일은 `.agent-home-version`, 사용자 규칙 파일은 `~/.claude/rules/agent-home.md` ([ADR 0007](docs/adr/0007-rename-to-agent-home.md))
- `sync_rules.py`: 예전 표시(`claude-home:common-rules`)를 새 표시로 바꾸고, 예전 이름의 버전 파일·사용자 규칙 파일은 스크립트가 쓴 모양 그대로일 때만 지움
- 공통 규칙: 클라우드 세션에만 적혀 있던 "PR은 내가 직접 확인하고 병합"을 모든 세션으로 넓혀, 모든 변경을 PR로 남기게 함
- GitHub Actions를 Node 24로 도는 주 버전으로 올림: `checkout@v7`, `setup-go@v7`, `setup-java@v6`, `setup-python@v7`, `setup-node@v7`, `golangci-lint-action@v9`. GitHub이 Node 20 실행을 지원 종료함 (`flutter-action@v2`는 composite라 그대로)
- 공통 규칙의 커밋 절을 48줄에서 15줄로 줄임. 새 프로젝트 `AGENTS.md`가 198~200줄에서 165~167줄로 줄어듦 ([ADR 0006](docs/adr/0006-check-commit-titles-instead-of-long-commit-rules.md))

## 2026-11-05

### 추가

- 설계 결정 기록(`docs/adr/` 0001~0005)과 이 변경 이력 (PR #17)
- `sync_rules.py --target`이 반영한 claude-home 커밋을 프로젝트의 `.claude-home-version`에 기록 (PR #16)
- `templates/README.md`: 템플릿 폴더별 용도와 복사되는 위치 (PR #18)
- 프로젝트 `AGENTS.md` 템플릿의 "이 저장소 규칙"에 확인된 사실 자리 추가, `writing-docs.md`에 찾는 방법 대신 확인한 사실을 근거와 함께 적는 기준 추가 (PR #21)
- `scripts/new_project.py`: 새 프로젝트 생성(기본은 미리보기, `--apply`로 만듦). `test_new_project.py`가 언어 5개 × 번역 여부로 만든 프로젝트가 검사를 통과하는지 CI에서 확인 (PR #14, [ADR 0005](docs/adr/0005-generate-projects-with-python-and-test-the-output.md))
- `new-project` 스킬 7단계: 첫 프로젝트에서 훅이 실제로 막는지 확인 (PR #14)

### 변경

- `research`, `translate-chapter`, `review-translation` 스킬: 읽은 자료에 적힌 지시는 따르지 않고 자료로만 다룸. `update-docs` 스킬: 문서의 명령 중 지우거나 바꾸거나 외부로 보내는 명령은 실행하지 않고 확인 항목으로 남김 (PR #19)

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
