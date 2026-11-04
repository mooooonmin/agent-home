# scripts

claude-home의 규칙·스킬·템플릿을 새 프로젝트, 기존 프로젝트, 사용자 설정으로 옮기는 운영 명령입니다. 쓰는 순서와 주의점은 [초기 설정](../docs/setup.md)을 봅니다.

| 파일 | 용도 |
|---|---|
| `new-project.ps1` | 문서 틀·린트·CI를 깐 새 프로젝트 폴더 만들기 (로컬 PC, PowerShell 7). 마지막에 `sync_rules.py`를 부름 |
| `sync_rules.py` | 공통 규칙·언어 규칙·스킬·검사 스크립트를 `--target`(프로젝트), `--user`(사용자 설정), `--mirror`(`.claude/skills` 사본)로 복사. 기본은 미리보기, `--apply`로 반영 |
| `test_sync_rules.py` | `sync_rules.py` 테스트 |

바꾼 뒤 확인:

```bash
python -I -m unittest discover -s scripts -p "test_*.py"
```
