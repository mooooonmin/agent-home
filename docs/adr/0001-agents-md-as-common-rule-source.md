# 0001. 공통 규칙의 원본을 AGENTS.md에 두고 Claude Code·Codex가 함께 읽는다

- 상태: 채택
- 날짜: 2026-11-04

## 배경

Claude Code와 Codex를 함께 쓰기로 했습니다. 그때까지 공통 규칙은 `.claude/rules/`에 있었는데, 이 위치는 Claude Code만 읽습니다. Codex 소스(`openai/codex`의 `core/src/agents_md.rs`)를 보면 Codex는 지시 파일로 `AGENTS.md`만 읽고(루트부터 작업 폴더까지, 기본 32KiB), 스킬은 `.agents/skills/`에서 읽습니다. Claude Code 공식 문서(memory)는 `CLAUDE.md`가 있으면 `AGENTS.md`를 따로 읽지 않으며, 대신 `CLAUDE.md`에 `@AGENTS.md` 줄을 넣는 방법을 안내합니다.

## 결정

- 항상 지킬 공통 규칙은 `AGENTS.md`의 `claude-home:common-rules` 표시 사이에 둡니다. `CLAUDE.md`는 `@AGENTS.md` 한 줄로 둡니다.
- 스킬 원본은 `.agents/skills/`에 두고, 같은 내용을 `.claude/skills/`에 복사합니다. 두 폴더가 다르면 저장소 검사가 실패합니다.
- 해당 파일을 다룰 때만 필요한 규칙은 `.claude/rules/`의 `paths` 규칙으로 둡니다. Codex는 공통 규칙의 표를 보고 직접 읽습니다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| `.claude/rules/`만 유지 | 바꿀 것이 없음 | Codex가 공통 규칙을 읽지 못함 |
| 규칙 파일을 따로 두고 `AGENTS.md`에 내용을 생성해 넣기 | 파일별로 고치기 쉬움 | 생성 단계와 어긋남 검사가 필요하고, Claude Code가 같은 규칙을 두 번 읽게 됨 |
| `.claude/skills`를 `.agents/skills`의 심볼릭 링크로 | 사본이 필요 없음 | Windows 클론에서 심볼릭 링크가 불안정함 |

## 결과

- 두 도구가 같은 원본을 읽습니다. 이 세션에서 Claude Code가 `@AGENTS.md`로 공통 규칙을 읽는 것을 확인했습니다. Codex에서의 동작은 미확인입니다.
- `paths` 규칙은 Codex가 자동으로 읽지 않아, Codex는 표의 안내를 따르는 만큼만 지킵니다.
- 근거: PR #8, #9
