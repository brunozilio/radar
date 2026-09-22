import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  globalIgnores([
    ".next/**",
    "cloudflare/index.js",
    "outputs/**",
    "projection-runtime/**",
    "next-env.d.ts",
  ]),
]);
