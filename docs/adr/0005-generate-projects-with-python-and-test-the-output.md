# 0005. 새 프로젝트는 Python 스크립트로 만들고 생성 결과를 CI 테스트로 보장한다

- 상태: 채택 (PowerShell `scripts/new-project.ps1`을 대체)
- 날짜: 2026-11-05

## 배경

claude-home의 목적은 나중에 새 프로젝트를 만들 때 기준을 깔고 시작하는 것입니다. 그런데 생성 경로인 `new-project.ps1`은 구조를 바꾼 뒤 한 번도 실행하지 못했고(클라우드에서 PowerShell 실행이 막힘), 규칙·템플릿을 고칠 때 생성 결과가 깨지는지 확인할 방법이 없었습니다.

## 결정

- `scripts/new_project.py`로 옮깁니다. 기본은 미리보기, `--apply`로 만듭니다. 규칙·스킬·검사·훅은 `sync_rules.py`의 함수를 그대로 씁니다.
- `scripts/test_new_project.py`가 언어 5개 × 번역 여부 10가지 조합으로 실제 템플릿에서 프로젝트를 만들고, 만든 프로젝트에서 저장소 검사·훅 테스트가 통과하는지 CI에서 확인합니다.
- Windows·Codex에서의 훅 동작은 `new-project` 스킬 7단계에서 첫 프로젝트를 만들 때 확인합니다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| PowerShell 유지 | 고칠 것이 적음 | 클라우드·CI에서 시험할 수 없고, PowerShell 7 설치가 필요 |
| cookiecutter·copier 같은 생성 도구 | 기능이 많음 | 새 의존성. 규칙 동기화(`sync_rules.py`)와 따로 놀게 됨 |

## 결과

- Python 3.11만 있으면 되고 PowerShell은 필요 없습니다.
- 규칙·템플릿을 고치다 새 프로젝트가 깨지면 CI가 잡습니다.
- 근거: PR #14
