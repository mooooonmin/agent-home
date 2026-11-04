---
paths:
  - "**/*.dart"
  - "**/pubspec.yaml"
  - "**/analysis_options.yaml"
---

# Dart / Flutter 규칙

기준: [Effective Dart](https://dart.dev/effective-dart). 린트는 `flutter_lints`에 엄격 모드를 더하고, 포맷은 `dart format`에 맡깁니다. 템플릿: claude-home의 `templates/lint/dart/analysis_options.yaml`

## 기본

- 이름: 타입 `UpperCamelCase`, 변수·함수 `lowerCamelCase`, 파일·폴더 `snake_case.dart`. 상수도 `lowerCamelCase`입니다.
- 다시 할당하지 않는 변수는 `final`, 컴파일 시점 상수는 `const`로 둡니다.
- null 안전성을 지킵니다. `!`(null 단언)는 확실할 때만 쓰고, 보통은 `?.`, `??`, 일찍 반환으로 처리합니다.
- 공개 API에는 반환 타입과 매개변수 타입을 적습니다. `dynamic`은 피합니다.
- 비동기는 `async`/`await`를 쓰고, 기다리지 않는 `Future`를 남기지 않습니다(필요하면 `unawaited`).
- 문자열은 작은따옴표를 쓰고, 조합은 `'$name'`처럼 보간을 씁니다.
- 출력은 `print` 대신 `debugPrint`나 로거를 씁니다.

## Flutter

- 위젯은 작게 나누고, 큰 `build` 메서드 안의 헬퍼 메서드보다 별도 위젯 클래스를 선호합니다.
- 바뀌지 않는 위젯에는 `const` 생성자를 씁니다.
- 상태는 저장소가 쓰는 방식(Provider, Riverpod, Bloc 등)을 따르고, UI와 비즈니스 로직을 나눕니다.
- `BuildContext`를 `await` 뒤에 쓸 때는 `if (!context.mounted) return;`으로 확인합니다.
- 플랫폼 코드(`android/`, `ios/`)를 건드리는 기능은 해당 플랫폼 빌드도 확인합니다.

## 실행

```bash
dart format .        # 포맷
flutter analyze      # 린트
flutter test         # 테스트
```
