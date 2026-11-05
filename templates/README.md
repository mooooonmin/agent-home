# templates

새 프로젝트와 기존 프로젝트에 넣는 파일의 원본입니다. 자리표시(`<...>`)가 들어 있으므로 여기서 실제 값으로 채우지 않습니다. 새 프로젝트는 `scripts/new_project.py`가, 기존 프로젝트는 `scripts/sync_rules.py`가 알맞은 위치로 복사합니다.

| 폴더·파일 | 용도 | 프로젝트에 들어가는 곳 |
|---|---|---|
| `AGENTS.project.md`, `CLAUDE.project.md` | 저장소 안내와 `@AGENTS.md` | `AGENTS.md`(아래에 공통 규칙이 붙음), `CLAUDE.md` |
| `agent-settings/` | 훅을 넣은 Claude Code·Codex 설정 | `.claude/settings.json`, `.codex/hooks.json` (없을 때만) |
| `ci/` | 저장소 검사·훅 스크립트와 테스트, GitHub Actions. [자세히](ci/README.md) | `scripts/`, `.github/workflows/` |
| `lint/` | 언어별 린트·포맷·계층 검사 설정, `.editorconfig`, `.gitattributes`, `.gitignore`. [자세히](lint/README.md) | 프로젝트 루트 |
| `docs/` | README, 폴더 README, CHANGELOG, ADR, 실행 계획 템플릿 | `README.md`, `CHANGELOG.md`, `docs/` |
| `translation-repo/` | 번역 저장소용 README·NOTICE·TRANSLATION.md | 번역 저장소 루트 |

바꾼 뒤 확인(새 프로젝트가 깨지지 않는지 포함):

```bash
python -I -m unittest discover -s scripts -p "test_*.py"
```
