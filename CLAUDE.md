# claude-home

내 공통 규칙·명령어·용어집·템플릿을 모아 둔 저장소입니다. 규칙의 **원본**은 여기 있고, 다른 프로젝트와 `~/.claude/`에는 복사해서 씁니다.

## 규칙

규칙은 `.claude/rules/`에 있고 Claude Code가 자동으로 읽습니다.

| 파일 | 내용 | 언제 읽히나 |
|---|---|---|
| `basics.md` | 소통, 작업 방식, 비밀값 | 항상 |
| `coding.md` | 코딩 스타일, 설계 원칙, 오류 처리, 테스트 | 항상 |
| `docs.md` | 문서를 코드와 함께 최신으로 유지하는 규칙 | 항상 |
| `git.md` | 커밋과 PR | 항상 |
| `translation.md` | 번역 원칙 | `.md`, `.ipynb` 파일을 다룰 때 |
| `lang/*.md` | Java, Python, JS/TS, Dart, Go 규칙 | 해당 언어 파일을 다룰 때 |

용어집은 `glossary/`에 있습니다. 번역할 때 해당 분야 파일을 먼저 읽습니다.

## 이 저장소에서 작업할 때

- 다른 저장소에 속하지 않는 결과물(조사, 초안, 메모)은 `notes/`에 `YYYY-MM-DD-주제.md`로 저장합니다.
- 규칙 파일을 고치면 `README.md`의 구조 설명과 위 표도 함께 고칩니다.
- `templates/` 아래 파일은 자리표시(`<...>`)가 들어간 원본입니다. 실제 값으로 채우지 않습니다.
- 커밋 전에 문서 링크를 검사합니다: `python -I templates/ci/check-doc-links.py --exclude templates`
