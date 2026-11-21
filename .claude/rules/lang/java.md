---
paths:
  - "**/*.java"
  - "**/build.gradle"
  - "**/build.gradle.kts"
---

# Java 규칙

기준: [Google Java Style](https://google.github.io/styleguide/javaguide.html)에 4칸 들여쓰기(AOSP 변형). 포맷은 Spotless + google-java-format(AOSP)에 맡깁니다. 템플릿: agent-home의 `templates/lint/java/spotless.gradle`

## 기본

- Java 17 이상 기능을 씁니다: `record`(값 객체, DTO), `switch` 식, 텍스트 블록, `var`(타입이 오른쪽에서 분명할 때만).
- 이름: 클래스 `PascalCase`, 메서드·변수 `camelCase`, 상수 `UPPER_SNAKE_CASE`, 패키지 소문자.
- 와일드카드 import(`import x.*`)를 쓰지 않습니다. 자동 생성 코드(QueryDSL `Q*` 등)는 예외입니다.
- `null`을 반환하지 말고 `Optional`(반환값 한정)이나 빈 컬렉션을 돌려줍니다. `Optional`을 필드·매개변수로 쓰지 않습니다.
- 컬렉션은 가능하면 `List.of`, `Map.of`, `.toList()`로 불변으로 만듭니다.
- 체크 예외를 `catch (Exception e) {}`로 삼키지 않습니다. 감쌀 때는 원인(`cause`)을 넘깁니다.

## Spring Boot

- 의존성은 **생성자 주입**만 씁니다(`@RequiredArgsConstructor` + `private final`). 필드 `@Autowired`는 쓰지 않습니다.
- 계층: `controller`(HTTP 입출력·검증) → `service`(비즈니스 로직·트랜잭션) → `repository`(DB). 컨트롤러에 로직을, 엔티티에 HTTP 개념을 넣지 않습니다.
- 엔티티를 API 응답으로 바로 내보내지 않고 DTO(`record`)로 바꿉니다.
- 요청 검증은 `@Valid` + Bean Validation 애너테이션으로 하고, 예외는 `@RestControllerAdvice`에서 한곳에서 처리합니다.
- 계층 방향은 ArchUnit 테스트로 강제합니다. 템플릿: agent-home의 `templates/lint/java/ArchitectureTest.java`
- `@Transactional`은 서비스 계층에 둡니다. 조회 전용은 `@Transactional(readOnly = true)`.
- JPA: 연관관계는 기본 `LAZY`, N+1이 생기면 fetch join이나 `@EntityGraph`로 풉니다. 엔티티에 `@Setter`와 `@Data`를 붙이지 않습니다.
- 설정값은 `application.yml` + `@ConfigurationProperties`로 받고, 비밀값은 환경 변수로 넣습니다.

## 테스트

- JUnit 5 + AssertJ. 단위 테스트는 Spring 컨텍스트 없이, 통합 테스트만 `@SpringBootTest`/`@DataJpaTest`.
- 테스트 이름은 `@DisplayName("한국어 설명")`이나 `메서드_상황_기대결과` 형식으로 씁니다.

## 실행

```bash
./gradlew spotlessApply   # 포맷
./gradlew test            # 테스트
./gradlew build           # 전체 빌드
```
