# 실행 계획

여러 세션에 걸치는 작업의 계획과 기록입니다. 기능 동작은 `README.md`와 `docs/`, 설계 결정은 [ADR](../adr/)이 담당합니다.

## 진행 중

| 계획 | 목표 | 시작 |
|---|---|---|
| [<제목>](active/<파일>.md) | <한 줄> | YYYY-MM-DD |

## 완료

| 기록 | 범위 | 근거 |
|---|---|---|
| [<제목>](completed/<파일>.md) | <한 줄> | 커밋 `<sha>` |

## 관리 규칙

- 새 계획은 [plan-template.md](plan-template.md)를 복사해 `active/`에 만들고 위 표에 추가합니다.
- 끝나면 최종 커밋과 검증 결과를 적고 `completed/`로 옮긴 뒤 표를 옮깁니다.
- 당장 하지 않을 개선 후보는 [tech-debt-tracker.md](tech-debt-tracker.md)에 적습니다.
