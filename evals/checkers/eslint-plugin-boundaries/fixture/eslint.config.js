// Docs: https://github.com/javierbrea/eslint-plugin-boundaries
//       https://www.jsboundaries.dev/docs/rules/dependencies/
//       https://www.jsboundaries.dev/docs/guides/typescript-support/
// Pattern: hexagonal (kit/layouts/hexagonal.md). Rule: domain may not import adapters.
import boundaries from "eslint-plugin-boundaries";
import typescriptParser from "@typescript-eslint/parser";

export default [
  {
    files: ["src/**/*.ts"],
    languageOptions: { parser: typescriptParser },
    plugins: { boundaries },
    settings: {
      "import/resolver": { typescript: { alwaysTryTypes: true } },
      "boundaries/elements": [
        { type: "domain", pattern: "src/domain" },
        { type: "adapters", pattern: "src/adapters" },
      ],
    },
    rules: {
      "boundaries/dependencies": [
        2,
        {
          default: "allow",
          policies: [
            {
              from: { element: { type: "domain" } },
              disallow: { to: { element: { type: "adapters" } } },
            },
          ],
        },
      ],
    },
  },
];
