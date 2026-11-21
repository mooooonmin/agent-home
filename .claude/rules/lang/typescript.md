---
paths:
  - "**/*.{ts,tsx,js,jsx,mjs,cjs}"
  - "**/package.json"
  - "**/tsconfig*.json"
---

# JavaScript / TypeScript 규칙

기준: 새 코드는 **TypeScript strict 모드**로 씁니다. 린트는 ESLint + typescript-eslint, 포맷은 Prettier에 맡깁니다. 템플릿: agent-home의 `templates/lint/typescript/`

클린 코드 원칙은 직접 번역한 [clean-code-javascript-ko](https://github.com/mooooonmin/clean-code-javascript-ko)를 따릅니다.

## 기본

- `tsconfig.json`에 `"strict": true`, `"noUncheckedIndexedAccess": true`를 켭니다.
- `any`를 쓰지 않습니다. 모르는 값은 `unknown`으로 받고 좁혀서 씁니다. 타입 단언(`as`)과 non-null 단언(`!`)은 최소화합니다.
- 변수는 `const`가 기본이고, 다시 할당할 때만 `let`을 씁니다. `var`는 쓰지 않습니다.
- 비교는 `===`만 씁니다. 기본값은 `||` 대신 `??`, 안전한 접근은 `?.`을 씁니다.
- 이름: 변수·함수 `camelCase`, 타입·클래스·컴포넌트 `PascalCase`, 상수 `UPPER_SNAKE_CASE`, 파일은 저장소 방식을 따릅니다.
- 모듈은 ES Modules(`import`/`export`)를 씁니다. 기본 내보내기(`export default`)보다 이름 있는 내보내기를 선호합니다.
- 비동기는 `async`/`await`로 쓰고, 기다리지 않는 프로미스를 남기지 않습니다. 병렬이 필요하면 `Promise.all`.
- 외부 입력(API 응답, 폼, 환경 변수)은 경계에서 스키마(zod 등)로 검증한 뒤 타입을 믿습니다.
- 배열·객체는 바꾸지 말고 새로 만듭니다(전개 연산자, `map`/`filter`).

## React (쓰는 경우)

- 함수 컴포넌트와 훅만 씁니다. 컴포넌트 하나에 역할 하나.
- 파생 값은 상태로 두지 말고 렌더링 중에 계산합니다. `useEffect`는 외부 시스템과 동기화할 때만 씁니다.
- 목록 `key`에 배열 인덱스를 쓰지 않습니다.

## 테스트

- Vitest(또는 저장소에 있는 Jest)를 씁니다. 화면은 Testing Library로 사용자 관점에서 검증합니다.

## 실행

```bash
npx prettier --write .   # 포맷
npx eslint .             # 린트
npx tsc --noEmit         # 타입 검사
```
