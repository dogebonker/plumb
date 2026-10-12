// Docs: https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md
//       https://github.com/sverweij/dependency-cruiser/blob/main/doc/options-reference.md
// Pattern: hexagonal (kit/layouts/hexagonal.md). Rule: domain may not import adapters.
module.exports = {
  forbidden: [
    {
      name: "domain-not-to-adapters",
      comment: "src/domain is the innermost ring; it may not depend on src/adapters",
      severity: "error",
      from: { path: "^src/domain/" },
      to: { path: "^src/adapters/" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    // Keep type-only imports, which vanish after compilation, in the graph.
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
  },
};
