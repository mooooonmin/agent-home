# 0007. 저장소 이름을 agent-home으로 바꾼다

- 상태: 채택
- 날짜: 2026-11-21

## 배경

이 저장소의 규칙·스킬·훅은 Claude Code와 Codex가 함께 씁니다([0001](0001-agents-md-as-common-rule-source.md), [0003](0003-enforce-branch-and-checks-with-hooks.md)). 그런데 이름 `claude-home`은 특정 도구에 묶인 인상을 줍니다. 2026-11-21에 저장소를 공개로 바꾸면서, 처음 보는 사람도 용도를 알 수 있는 도구 중립적인 이름이 필요해졌습니다.

이름은 문서뿐 아니라 동작에도 쓰입니다. 프로젝트와 사용자 설정에 복사되는 공통 규칙의 경계 표시(`claude-home:common-rules`), 프로젝트에 남는 `.claude-home-version`, 사용자 규칙 파일 `~/.claude/rules/claude-home.md`입니다. 바꾼 날 기준으로 이 PC의 프로젝트 폴더와 내 GitHub 저장소 중 이 규칙을 복사해 간 곳은 없었습니다. 다만 다른 PC의 사용자 설정에는 남아 있을 수 있습니다.
## 결정

- 저장소 이름을 `agent-home`으로 바꿉니다. 기존의 "home"(규칙의 원본이 사는 곳) 개념은 그대로 두고, 도구 이름만 뺍니다.
- 표시·파일 이름도 같이 바꿉니다: `agent-home:common-rules`, `.agent-home-version`, `~/.claude/rules/agent-home.md`.
- `sync_rules.py`는 예전 표시를 찾으면 그 자리를 새 표시로 바꿉니다. 예전 이름의 버전 파일·사용자 규칙 파일은 스크립트가 쓴 모양 그대로일 때만 지우고, 아니면 알립니다.
- 지난 기록(ADR 0001~0006, `notes/`, CHANGELOG의 지난 항목)은 당시 사실이라 예전 이름 그대로 둡니다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| 이름만 바꾸고 표시·파일 이름은 유지 | 스크립트를 고칠 필요가 없음 | 복사된 파일마다 예전 이름이 계속 남아 이름을 바꾼 의미가 줄어듦 |
| 예전 표시를 읽지 않음 | 코드가 단순함 | 다른 PC의 `~/.codex/AGENTS.md`에 예전 표시가 있으면 공통 규칙이 두 번 붙음 |
| `dotagents`, `house-rules`, `harbor` 등 다른 이름 | 각자 개성이 있음 | "home" 개념이 끊기거나, 처음 보는 사람에게 용도가 덜 드러남 |

## 결과

- GitHub 저장소 이름은 이 변경을 병합한 뒤 바꿉니다. GitHub가 예전 주소를 새 주소로 넘겨 주므로 기존 링크(예: PEIM `AGENTS.md`의 PR #23 링크)는 그대로 열립니다.
- 받아 둔 폴더는 이름과 원격 주소를 직접 바꿔야 합니다(`docs/setup.md`의 문제 해결).
- 공개 저장소가 되어 GitHub Free로도 저장소 규칙(ruleset)을 쓸 수 있습니다. [0003](0003-enforce-branch-and-checks-with-hooks.md)에서 요금제 때문에 미룬 서버 쪽 보호를 이제 켤 수 있습니다(`docs/setup.md`의 GitHub 저장소 규칙).
