# 하네스 엔지니어링 기준으로 본 claude-home 검토

한 줄 요약: claude-home에는 하네스 엔지니어링의 "안내(guides)" 쪽이 이미 잘 갖춰져 있습니다. 목차형 CLAUDE.md, 담당 문서, ADR·실행 계획, 저장소 검사가 그 예입니다. 비어 있는 곳은 두 가지입니다. 하나는 **작업 중에 자동으로 도는 확인(훅)** 이고, 다른 하나는 **세션 사이 인계와 동작 확인 절차**입니다. 이와 별개로, 새 프로젝트로 복사된 규칙이 그 프로젝트에 없는 `templates/` 경로를 가리키는 문제를 하나 찾았습니다.

## 고칠 만한 것 (우선순위 순)

| # | 제안 | 지금 상태 (근거) | 외부 근거 | 크기 |
|---|---|---|---|---|
| 1 | **복사된 규칙의 끊긴 경로 고치기.** `/new-project`가 `pr-body.md`, `folder-README.md`도 복사하게 하고, 규칙의 `templates/...` 표기를 "claude-home의 `templates/...`" 또는 프로젝트 안 경로로 바꿈 | `git.md`는 `templates/pr-body.md`를, `docs.md`는 `templates/docs/folder-README.md`를 가리키지만 `scripts/new-project.ps1`은 두 파일을 복사하지 않음. `coding.md`, `lang/*.md`도 `templates/lint/...`를 가리킴 | 저장소 밖에 있는 것은 에이전트에게 없는 것과 같음 (OpenAI "repository as system of record", 2차 자료) | 작음 |
| 2 | **훅으로 확인을 작업 루프 안에 넣기.** `settings.json` 템플릿에 언어별 PostToolUse 포맷터, 빠른 검사만 도는 Stop 훅(실패 시 `exit 2`)을 추가 | `.claude/settings.json`에는 권한 규칙만 있고 훅이 없음. 포맷·검사는 CI에서만 강제됨 | 공식: "If you keep adding emphasis to a `CLAUDE.md` line and Claude still misses it, that's a sign the line belongs in a hook." / Stop 훅 예시 (best-practices, hooks-guide) | 중간 |
| 3 | **세션 시작·끝 순서.** `CLAUDE.project.md`에 짧은 절차를 둠 (시작: `git log`와 진행 중 계획 읽기 → 기존 기능이 도는지 먼저 확인 / 끝: 계획 갱신 → 커밋). 실행 계획 템플릿에는 덮어쓰는 "현재 상태"(마지막 커밋, 검사 결과, 다음 할 일)를 추가 | `docs/exec-plans/`에 계획은 있지만 다음 세션이 어디서 이어 갈지 적는 칸이 없음. `docs.md`는 작업 일지를 금지함(유지) | Anthropic: 세션 시작 시 git 로그·진행 파일 읽기, 기능 하나씩, 끝날 때 커밋과 진행 기록 | 작음 |
| 4 | **동작 확인 칸.** `CLAUDE.project.md`에 "앱을 띄워 사용자처럼 확인하는 방법" 칸을 추가. 완료 보고에는 실행한 명령과 출력을 근거로 붙임 | `basics.md`의 "검증함"은 명령을 적게 하지만, 프로젝트마다 어떻게 실행해 확인하는지 적는 자리가 없음 | 공식: "ask Claude for *evidence*", `/verify` / Anthropic: 단위 테스트만으로는 기능이 안 되는 걸 놓쳤고, 사용자처럼 E2E로 시험하게 하자 나아짐 | 작음 |
| 5 | **PR 전 독립 리뷰.** `git.md`에 "PR을 만들기 전에 `/code-review`" 한 줄 추가 | `git.md`에 리뷰 단계가 없음 | 공식: "`/code-review` reviews the diff in a fresh subagent that never saw your conversation." | 아주 작음 |
| 6 | **"두 번 지적하면 검사로" 승격 규칙.** 같은 지적이 두 번 나오면 린트·테스트·훅으로 만들고, 당장 못 하면 `tech-debt-tracker.md`에 적음 | `coding.md`에 "규칙은 검사로 강제"는 있지만 언제 승격할지 기준이 없음 | 공식: CLAUDE.md에 넣을 것 중 "Anything you've had to correct twice already" / OpenAI·Fowler의 기계적 강제(2차 자료) | 아주 작음 |
| 7 | **commands → skills 이전** (급하지 않음) | `.claude/commands/`에 명령 5개 | 공식: commands는 "the older format and still works ... Prefer a skill for new work" | 중간 (스크립트·문서 참조도 함께 수정) |
| 8 | **규칙 다이어트** (판단 필요) | `lang/python.md`의 이름 규칙·`pathlib`는 `ruff.toml`의 `N`, `PTH` 규칙과 겹침 | 공식: "Could it find this by reading the code? Would it actually go and look? If both are yes, leave it out." | 작음 |
| 9 | **정기 정리** (선택) | `/update-docs`는 수동으로만 실행 | OpenAI "garbage collection"(2차 자료), Fowler의 AI 리뷰를 주기적 정리로 쓰는 예(2차 자료) | 작음. 클라우드 정기 실행은 사용량을 씀 |

## 이미 갖춘 것

| 하네스 개념 | claude-home에서 해당하는 것 |
|---|---|
| 지도이지 설명서가 아님 (짧은 진입 문서 + 담당 문서) | `templates/CLAUDE.project.md`("이 파일은 목차입니다"), `docs.md`의 "주제 하나, 담당 문서 하나" |
| 필요할 때만 읽히는 규칙 | `lang/*.md`, `translation.md`의 `paths:` |
| 저장소가 기록의 원본 | `docs/adr/`, `docs/exec-plans/active·completed`, `tech-debt-tracker.md`, `CHANGELOG.md` |
| 기계적 강제, 고치는 방법을 담은 오류 메시지 | `repo_checks.py`(예: "생성 산출물은 커밋하지 않습니다 (.gitignore에 추가)"), ArchUnit·import-linter 템플릿, 언어별 CI |
| 성급한 완료 선언 막기 | `basics.md`의 구현함/검증함/배포함 구분, `git.md`의 "돌리지 않은 테스트를 통과했다고 쓰지 않습니다" |
| 문서 정리 | `/update-docs` |
| AGENTS.md 호환 | 템플릿의 `@AGENTS.md` 가져오기. 공식 문서도 이 방식을 안내하며, `CLAUDE.md`가 있으면 기본적으로 `AGENTS.md`를 따로 읽지 않음 |
| 항상 읽히는 양 | `CLAUDE.md`와 규칙 4개를 합쳐 233줄이고 각 파일은 70줄 이하. 공식 권장("under 200 lines per CLAUDE.md file") 범위 안 |

## 받아들이지 않는 것

- **`feature_list.json`, `Makefile` 중심 구조**(learn-harness-engineering의 점검 항목): 앱 하나를 오래 자율로 만드는 경우에 맞춘 구조입니다. 번역 저장소처럼 성격이 다른 프로젝트까지 함께 쓰는 claude-home의 공통 틀로는 무겁습니다. 장기 자율 개발 프로젝트에서만 따로 검토합니다.
- **"자주 실패하는 테스트로 병합을 막지 않는다"**(OpenAI, 2차 자료): 사람이 확인하고 병합한다는 `git.md` 규칙과 맞지 않습니다.
- **처음부터 큰 하네스**: HumanLayer는 "간단히 시작해 필요할 때 더한다"를 권하고(2차 자료), Fowler는 안내와 확인이 늘어나면 서로 어긋날 수 있다고 지적합니다(2차 자료). 그래서 위 표도 작은 것부터 순서를 매겼습니다.

## 외부 기준 요약

- **Anthropic, "Effective harnesses for long-running agents"** (2025-11-26, 원문 확인): 첫 세션에서 환경을 깔고(`init.sh`, 진행 파일, 첫 커밋), 이후 세션은 기능 하나씩 진행하며 구조화된 기록을 남깁니다. 기능 목록은 JSON으로 둡니다("the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files"). 세션은 `pwd` → git 로그·진행 파일 읽기 → 우선순위 기능 선택 순서로 시작합니다.
- **Claude Code 공식 문서** (원문 확인): CLAUDE.md는 파일당 200줄 아래를 목표로 하고, 코드만 봐서는 알 수 없는 것만 적습니다. 반드시 지켜야 할 것은 훅·deny 규칙으로 둡니다. 확인 수단(테스트, 빌드 종료 코드, 린터, 스크린샷)을 주고 근거를 받습니다. 리뷰는 대화를 보지 않은 하위 에이전트로 합니다.
- **OpenAI, "Harness engineering: leveraging Codex in an agent-first world"** (2026-02-11, Ryan Lopopolo): 원문은 이 환경에서 접속이 막혀 읽지 못했고, [deusyu/harness-engineering](https://github.com/deusyu/harness-engineering)의 개념 정리(2차 자료)로 확인했습니다. 여섯 가지 개념을 제시합니다: 저장소가 기록의 원본, 지도이지 설명서가 아님(약 100줄 AGENTS.md), 기계적 강제, 에이전트가 읽기 쉬운 구조, 처리량에 맞춘 병합, 엔트로피 관리(주기적 정리).
- **Böckeler(martinfowler.com), "Harness engineering for coding agent users"** (2026-04-02): 원문은 이 환경에서 접속이 막혀 같은 저장소의 정리(2차 자료)로 확인했습니다. 안내(feedforward)와 확인(feedback)을 둘 다 갖춰야 하고, 각각을 결정적(린터, 타입 검사)인 것과 추론적(AI 리뷰)인 것으로 나눕니다. 셋 중 동작(behaviour) 하네스가 가장 약하다고 봅니다.
- **GitHub에서 널리 쓰이는 정리** (2026-11-03 기준 별 수): [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering)(약 23k)은 하네스를 지시·상태·검증·범위·세션 수명주기의 다섯 영역으로 나눕니다. [agentsmd/agents.md](https://github.com/agentsmd/agents.md)(약 25k)는 AGENTS.md 형식입니다. [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)(약 69k)는 팁 모음으로, 포맷용 PostToolUse 훅과 강제할 동작은 settings.json에 두라는 내용 등을 담고 있습니다. [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering)(약 5k)는 자료 목록입니다.

## 더 볼 것

- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): 장기 실행 하네스의 원형
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices): 결정적 강제와 검증
- [Claude Code memory](https://code.claude.com/docs/en/memory): CLAUDE.md 크기, `paths` 규칙, AGENTS.md
- [Claude Code hooks guide](https://code.claude.com/docs/en/hooks-guide): 포맷 훅, 보호 파일 차단, Stop 훅
- [Claude Code skills](https://code.claude.com/docs/en/skills): commands와 skills의 관계
- [OpenAI 원문](https://openai.com/index/harness-engineering/), [Fowler 원문](https://martinfowler.com/articles/harness-engineering.html): 이번에는 읽지 못함
- [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering): 다섯 영역 모델과 점검 스크립트(`tools/audit-harness.sh`)

## 확인 못 한 것

- OpenAI·Fowler·HumanLayer 원문: 이 클라우드 환경의 네트워크 정책 때문에 접속이 거부됨. 해당 내용은 모두 2차 자료 기준입니다.
- `audit-harness.sh`를 claude-home에 실제로 돌린 결과: 외부 코드 실행이 권한 검사에서 막혀 점검 항목만 읽고 직접 대조함.
- 제안 2의 훅이 로컬 Windows(`pwsh`·Git Bash)에서 그대로 동작하는지: 시험하지 않음.
- GitHub 별 수: 검색 API 값이며 시점에 따라 바뀜.
