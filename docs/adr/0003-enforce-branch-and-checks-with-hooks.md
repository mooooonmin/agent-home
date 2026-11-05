# 0003. 기본 브랜치 보호와 끝내기 전 검사를 두 도구 공용 훅으로 강제한다

- 상태: 채택
- 날짜: 2026-11-04

## 배경

"기본 브랜치에 바로 커밋하지 않는다", "검증한 만큼만 말한다"가 글로만 있었습니다. Claude Code 공식 문서(best-practices)는 강조해도 놓치는 규칙은 훅으로 옮기라고 합니다. Claude Code와 Codex는 훅 입력(표준 입력 JSON)과 막는 방식(종료 코드 2 + 표준 오류)이 같습니다(Codex 소스 `hooks/src/events/pre_tool_use.rs`, `stop.rs`).

## 결정

- 두 도구가 같은 스크립트(`templates/ci/agent_hooks.py`, 프로젝트에서는 `scripts/agent_hooks.py`)를 부릅니다.
  - `pre-bash`: `main`·`master`로 바로 커밋·푸시하는 git 명령을 막습니다. 새 저장소의 첫 커밋·첫 푸시는 허용합니다.
  - `stop`: 커밋하지 않은 변경이나 올리지 않은 커밋이 있으면 저장소 검사를 돌리고, 실패하면 끝내지 않게 합니다.
- Claude Code는 `.claude/settings.json`(셸 없이 실행하는 `args` 형식), Codex는 `.codex/hooks.json`(git으로 저장소 루트를 찾아 실행)에 설정합니다.
- 설정이 가리키는 훅 스크립트가 있는지 저장소 검사가 확인합니다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| 글로 된 규칙만 유지 | 할 일이 없음 | 지키는지가 모델 판단에 달림 |
| GitHub 저장소 규칙(ruleset) | 서버에서 확실히 막음 | 비공개 저장소는 GitHub Pro 이상 필요. 현재 Free라 쓸 수 없음 (설정 순서는 `docs/setup.md`에 둠) |
| git pre-commit 훅 | 사람에게도 적용 | 저장소마다 `core.hooksPath` 설정이 필요하고, 끝내기 전 검사는 할 수 없음 |

## 결과

- 셸 문장을 읽어 판단하므로 모든 우회를 막지는 못합니다. 서버 쪽 보호는 요금제가 바뀌면 추가합니다.
- Codex는 저장소 훅을 사용자가 `/hooks`에서 승인해야 실행합니다.
- 이 세션(Claude Code, 클라우드)에서 `main` 푸시가 막히는 것을 확인했습니다. Windows·Codex는 첫 새 프로젝트에서 확인합니다.
- 근거: PR #10, #11
