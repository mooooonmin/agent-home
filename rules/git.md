# 커밋과 PR 규칙

## 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/ko/) 형식에 한국어 설명을 씁니다.

```
<type>(<scope>): <한국어 설명>
```

- type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`
- 번역 저장소는 `docs(ko)`를 씁니다.
  - 예: `docs(ko): 9장 오류 처리 번역`
  - 예: `docs(ko): README를 장별 목차로 작성`
- 한 커밋에는 한 가지 일만 담습니다(번역은 보통 장 하나 = 커밋 하나).
- 설명은 "~ 번역", "~ 추가", "~ 수정"처럼 명사형으로 끝냅니다.

## 브랜치와 PR

- 기본 브랜치에 바로 커밋하지 말고 작업 브랜치를 만듭니다. 예: `translate/ch09`, `fix/broken-links`
- PR 본문은 `templates/pr-body.md`를 따릅니다.
- 클라우드 세션에서 만든 PR은 내가 직접 확인하고 병합합니다. 자동 병합은 켜지 않습니다.
