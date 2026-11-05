# claude-home 동작 확인 (로컬, 이후 클라우드)

한 줄 요약: 규칙·명령어 로드, 검사 도구 테스트, 저장소 검사는 모두 통과했습니다. 이번 확인은 클라우드가 아니라 **로컬 PC(Windows)** 의 Claude Code 세션에서 했으므로, 클라우드 고유 항목은 미확인입니다.

| 확인 | 명령·방법 | 결과 |
|---|---|---|
| 실행 환경 | `uname -s` | 로컬 Windows (`MINGW64_NT-10.0-26300`). 클라우드 VM 아님 |
| `CLAUDE.md` 로드 | 세션 컨텍스트 확인 | 읽힘 |
| 항상 읽히는 규칙 | 세션 컨텍스트 확인 | `basics.md`, `coding.md`, `docs.md`, `git.md` 읽힘 |
| 경로 조건 규칙 | 세션 컨텍스트 확인 | `translation.md`는 `.md` 파일을 다룰 때 읽힘. `lang/*.md`는 해당 언어 파일을 다루지 않아 이번에는 읽히지 않음(정상) |
| 명령어 | 세션의 사용 가능한 명령 목록 | `/new-project`, `/research`, `/review-translation`, `/translate-chapter`, `/update-docs` 모두 인식됨 |
| Python | `python --version` | 3.12.10 |
| GitHub CLI | `gh --version` | 2.103.3 |
| Git | `git --version` | 2.47.1 |
| PowerShell 7 | `pwsh` | 7.6.9 (로컬). 클라우드에는 없음(공식 문서 기준) |
| Flutter | `command -v flutter` | 있음 (로컬). 클라우드에는 없음(공식 문서 기준) |
| 검사 도구 테스트 | `python -I -m unittest discover -s templates/ci -p "test_*.py"` | 11개 통과 |
| 저장소 검사 | `python -I templates/ci/repo_checks.py --docs-exclude templates` | 문제 0개 (이 노트 추가 전·후 모두) |
| 브랜치 푸시와 PR | `test/cloud-smoke` 브랜치 푸시, PR 생성 | 로컬에서 수행 |
| 클라우드 세션에서 저장소 열기 | claude.ai/code에서 `mooooonmin/claude-home` 선택 | 미확인: 이번 확인을 로컬에서 진행함 |
| 클라우드의 규칙 로드·도구·푸시 | 클라우드 세션에서 위 항목 반복 | 미확인: 같은 이유 |

## 클라우드에서 확인한 결과

2026-11-05에 덧붙였습니다. 위 표에서 미확인으로 남은 클라우드 항목은 2026-11-03~05의 클라우드 세션(claude.ai/code, `mooooonmin/claude-home`)에서 확인했습니다. 그사이 구조가 바뀌어(명령어 → 스킬, 공통 규칙 → `AGENTS.md`) 위 표의 파일 이름 일부는 지금과 다릅니다.

| 확인 | 방법 | 결과 |
|---|---|---|
| 실행 환경 | `uname -s` | Linux (클라우드 VM) |
| 규칙 로드 (구조 변경 전) | 세션 컨텍스트 | `CLAUDE.md`와 `.claude/rules/` 4개 읽힘, `translation.md`는 `.md`를 다룰 때 읽힘 |
| 규칙 로드 (구조 변경 후) | 세션 컨텍스트 | `CLAUDE.md`의 `@AGENTS.md`로 공통 규칙이 읽힘. `code.md`, `writing-docs.md`는 해당 파일을 다룰 때 읽힘 |
| 도구 | `--version`, `command -v` | Python 3.13.18, gh 2.89.0, git 2.43.0 있음. `pwsh`, `flutter` 없음 |
| 작업 브랜치 푸시 | `git push -u origin <브랜치>` | 됨. PR #8~#14를 이 방식으로 올림 |
| 훅 | `git push --dry-run origin HEAD:main` | Claude Code가 실행 전에 훅을 불러 막음 |
| 검사 도구·저장소 검사 | 저장소 안내의 테스트·검사 명령 | 통과 |

남은 미확인(Codex, Windows)은 [하네스 검토 노트의 진행 결과](2026-11-03-harness-engineering-review.md#진행-결과)에 있습니다.
