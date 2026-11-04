# CI 템플릿

저장소 규칙을 로컬과 CI에서 같은 명령으로 검사합니다. 표준 라이브러리만 써서 설치할 것이 없습니다.

| 파일 | 용도 | 넣는 곳 |
|---|---|---|
| `repo_checks.py` | 생성물 커밋, 버전 고정, `latest` 태그, 충돌 표시, 셸 문법, 문서 링크, 공백 오류, 에이전트 지시 파일(`AGENTS.md` 크기, `CLAUDE.md`의 `@AGENTS.md`, 스킬 원본과 사본 일치)을 한 번에 검사 | `scripts/` |
| `check_doc_links.py` | 문서 내부 링크·이미지·제목 앵커 검사 (`repo_checks.py`가 불러 씀) | `scripts/` |
| `test_checks.py` | 위 두 검사 도구의 테스트 | `scripts/` |
| `checks.yml` | 저장소 검사 GitHub Actions | `.github/workflows/` |
| `lang/<언어>.yml` | 언어별 빌드·포맷·린트·테스트 GitHub Actions (java, python, typescript, dart, go) | `.github/workflows/` |

새 프로젝트는 `scripts/new-project.ps1`이 이 파일들을 알맞은 위치에 넣어 줍니다. 검사 스크립트 세 개는 `scripts/sync_rules.py`가 넣고, 원본이 바뀌면 같은 명령으로 다시 반영합니다.

로컬에서 확인:

```bash
python -I scripts/repo_checks.py
python -I -m unittest discover -s scripts -p "test_checks.py"
```

자리표시 링크가 많은 폴더는 `--docs-exclude 폴더`로 문서 링크 검사에서만 빼고, 검사 자체가 필요 없는 폴더는 `--exclude 폴더`로 뺍니다. 검사 항목을 바꾸면 `test_checks.py`에도 테스트를 추가합니다.
