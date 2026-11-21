---
paths:
  - "**/*.go"
  - "**/go.mod"
---

# Go 규칙

기준: [Effective Go](https://go.dev/doc/effective_go)와 [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments). 포맷은 `gofmt`/`goimports`, 린트는 golangci-lint에 맡깁니다. 템플릿: agent-home의 `templates/lint/go/.golangci.yml`

## 기본

- 이름: 짧고 분명하게 짓습니다. 내보내는 이름은 `PascalCase`, 아니면 `camelCase`. 약어는 대소문자를 통일합니다(`userID`, `HTTPServer`).
- 패키지 이름은 소문자 한 단어이고, 패키지 이름을 반복하지 않습니다(`http.HTTPServer` 대신 `http.Server`).
- **오류는 반드시 확인합니다.** `_`로 버리지 않고, 감쌀 때는 `fmt.Errorf("무엇을 하다가: %w", err)`처럼 맥락을 붙입니다. 비교는 `errors.Is`/`errors.As`로 합니다.
- `panic`은 프로그램이 계속될 수 없는 경우에만 씁니다. 라이브러리 코드에서는 오류를 반환합니다.
- 인터페이스는 쓰는 쪽에서 작게 정의합니다. "인터페이스를 받고 구조체를 반환"합니다.
- 오래 걸리거나 취소될 수 있는 함수는 첫 인자로 `ctx context.Context`를 받습니다.
- 고루틴을 시작하면 끝나는 방법(취소, `WaitGroup`, `errgroup`)을 함께 만듭니다. 공유 상태는 채널이나 `sync.Mutex`로 보호합니다.
- 전역 변수와 `init()`을 최소화합니다.
- 운영체제마다 다른 경로는 `filepath`로 다룹니다(Windows 호환).

## 테스트

- 표 기반 테스트(table-driven test)와 `t.Run`을 씁니다. 동시성 코드는 `-race`로 돌립니다.

## 실행

```bash
gofmt -w . && goimports -w .   # 포맷
golangci-lint run              # 린트
go test -race ./...            # 테스트
```
