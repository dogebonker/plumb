// Docs: https://github.com/feature-sliced/steiger
// Pattern: fsd (kit/layouts/fsd.md). The recommended config's fsd/forbidden-imports forbids imports from
// higher layers and cross-imports between slices on one layer.
import { defineConfig } from "steiger";
import fsd from "@feature-sliced/steiger-plugin";

export default defineConfig([...fsd.configs.recommended]);
