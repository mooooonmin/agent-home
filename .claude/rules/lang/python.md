---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
---

# Python 규칙

기준: [PEP 8](https://peps.python.org/pep-0008/). 린트와 포맷은 [ruff](https://docs.astral.sh/ruff/)에 맡깁니다. 템플릿: agent-home의 `templates/lint/python/ruff.toml`

## 기본

- Python 3.11 이상을 기준으로 씁니다.
- 이름: 함수·변수 `snake_case`, 클래스 `PascalCase`, 상수 `UPPER_SNAKE_CASE`, 비공개는 앞에 `_`.
- 공개 함수에는 **타입 힌트**를 붙입니다. 내장 제네릭(`list[str]`, `dict[str, int]`)과 `X | None`을 씁니다.
- 경로는 `os.path` 대신 `pathlib.Path`, 문자열 조합은 f-string을 씁니다.
- 데이터 묶음은 딕셔너리 대신 `@dataclass`(필요하면 `frozen=True`)나 Pydantic 모델로 만듭니다.
- 파일·연결은 `with` 문으로 엽니다. 파일을 열 때는 `encoding="utf-8"`을 명시합니다(Windows 기본 인코딩 문제 방지).
- `except:`나 `except Exception: pass`로 오류를 삼키지 않습니다. 잡을 예외를 구체적으로 적습니다.
- 기본값으로 가변 객체(`def f(x=[])`)를 쓰지 않습니다.
- 출력은 `print` 대신 `logging`을 씁니다(일회성 스크립트 제외).
- 스크립트 진입점은 `if __name__ == "__main__":` 아래에 둡니다.

## 구조

- 계층이 있는 프로젝트는 import-linter로 의존 방향을 강제합니다. 템플릿: agent-home의 `templates/lint/python/importlinter.toml`

## 환경과 의존성

- 프로젝트마다 가상환경을 씁니다(`uv` 또는 `python -m venv .venv`). `.venv/`는 커밋하지 않습니다.
- 의존성은 `pyproject.toml`에 적고 버전을 잠급니다(`uv.lock` 또는 `requirements.txt` 고정).

## 노트북(.ipynb)

- 셀은 위에서 아래로 한 번에 돌려도 동작해야 합니다.
- 비밀값을 셀에 적지 않고 환경 변수에서 읽습니다.
- 번역 저장소의 노트북은 코드 셀과 출력을 바꾸지 않습니다(번역 규칙 참고).

## 테스트

- pytest를 씁니다. 파일은 `tests/test_*.py`, 함수는 `test_무엇을_하면_어떻게_된다` 형식으로 짓습니다.

## 실행

```bash
ruff format .          # 포맷
ruff check --fix .     # 린트
pytest                 # 테스트
```
