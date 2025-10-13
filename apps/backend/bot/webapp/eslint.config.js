import js from "@eslint/js";
import htmlPlugin from "eslint-plugin-html";

export default [
  htmlPlugin.configs["flat/recommended"],
  {
    files: ["**/*.{js,mjs,cjs,jsx}"],
    ignores: ["dist/**", "node_modules/**"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        Telegram: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        FormData: "readonly",
        URL: "readonly"
      }
    },
    plugins: { html: htmlPlugin },
    rules: {
      ...js.configs.recommended.rules,
      "no-console": ["warn", { allow: ["error", "warn"] }],
      "no-undef": "error",
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }]
    }
  }
];
