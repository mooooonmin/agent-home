// 설치: npm i -D eslint @eslint/js typescript-eslint eslint-config-prettier prettier
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";

export default tseslint.config(
  { ignores: ["dist/", "build/", "coverage/", "node_modules/"] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  prettier, // 포맷 관련 규칙은 Prettier에 맡깁니다
);
