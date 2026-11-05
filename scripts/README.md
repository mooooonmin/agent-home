# scripts

claude-home의 규칙·스킬·템플릿을 새 프로젝트, 기존 프로젝트, 사용자 설정으로 옮기는 운영 명령입니다. 쓰는 순서와 주의점은 [초기 설정](../docs/setup.md)을 봅니다.

| 파일 | 용도 |
|---|---|
| `new_project.py` | 문서 틀·린트·CI·규칙·훅을 깐 새 프로젝트 폴더 만들기. 기본은 미리보기, `--apply`로 만듦. 규칙·스킬·검사 도구는 `sync_rules.py`의 함수로 넣음 |
| `test_new_project.py` | 모든 언어·번역 조합으로 만든 프로젝트가 저장소 검사와 훅 테스트를 통과하는지 확인 |
| `sync_rules.py` | 공통 규칙(`AGENTS.md` 부분, `code.md`, `writing-docs.md`)·언어 규칙·스킬·검사·훅 스크립트(훅 설정은 없을 때만)를 `--target`(프로젝트), `--user`(사용자 설정), `--mirror`(`.claude/skills` 사본)로 복사. 기본은 미리보기, `--apply`로 반영 |
| `test_sync_rules.py` | `sync_rules.py` 테스트 |

바꾼 뒤 확인:

```bash
python -I -m unittest discover -s scripts -p "test_*.py"
```
