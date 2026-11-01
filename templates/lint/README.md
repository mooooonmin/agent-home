# 린트·포맷 템플릿

규칙은 글보다 도구가 더 잘 지킵니다. 새 프로젝트를 만들거나 기존 프로젝트를 정리할 때 해당 언어 파일을 복사합니다.

| 파일 | 언어 | 넣는 곳 |
|---|---|---|
| [.editorconfig](.editorconfig) | 공통 | 프로젝트 루트 |
| [.gitattributes](.gitattributes) | 공통 (Windows 줄바꿈 통일) | 프로젝트 루트 |
| [java/spotless.gradle](java/spotless.gradle) | Java | `build.gradle`에 붙여 넣기 |
| [python/ruff.toml](python/ruff.toml) | Python | 프로젝트 루트 |
| [typescript/eslint.config.js](typescript/eslint.config.js), [.prettierrc.json](typescript/.prettierrc.json) | JS/TS | 프로젝트 루트 |
| [typescript/tsconfig.strict.json](typescript/tsconfig.strict.json) | TS | `tsconfig.json`에 합치기 |
| [dart/analysis_options.yaml](dart/analysis_options.yaml) | Dart/Flutter | 프로젝트 루트 |
| [go/.golangci.yml](go/.golangci.yml) | Go | 프로젝트 루트 |

기존 프로젝트에 처음 적용하면 포맷 변경이 많이 생깁니다. **포맷만 바꾸는 커밋을 따로** 만들고(`style: 포매터 적용`), 기능 변경과 섞지 않습니다.
