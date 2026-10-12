// Docs: https://github.com/un-ts/eslint-plugin-import-x/blob/master/docs/rules/no-restricted-paths.md
// Pattern: feature-folders (kit/layouts/feature-folders.md). Sibling rule: features may not import each other.
// `except` paths are relative to `from`.
import importX from "eslint-plugin-import-x";
import typescriptParser from "@typescript-eslint/parser";

export default [
  {
    files: ["src/**/*.ts"],
    languageOptions: { parser: typescriptParser },
    plugins: { "import-x": importX },
    settings: {
      "import-x/resolver": { typescript: { alwaysTryTypes: true } },
    },
    rules: {
      "import-x/no-restricted-paths": [
        "error",
        {
          zones: [
            { target: "./src/features/a", from: "./src/features", except: ["./a"], message: "feature a may not import another feature" },
            { target: "./src/features/b", from: "./src/features", except: ["./b"], message: "feature b may not import another feature" },
          ],
        },
      ],
    },
  },
];
