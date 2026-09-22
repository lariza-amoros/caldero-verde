import { build } from "esbuild";
import { fileURLToPath } from "node:url";
import { readFile } from "node:fs/promises";
import { dirname } from "node:path";

const entryPoint = fileURLToPath(new URL("../netlify/functions/api.ts", import.meta.url));
const outfile = fileURLToPath(new URL("../.netlify-build/api.mjs", import.meta.url));
const source = await readFile(entryPoint, "utf8");

await build({
  stdin: {
    contents: source,
    sourcefile: "api.ts",
    loader: "ts",
    resolveDir: dirname(entryPoint),
  },
  outfile,
  bundle: true,
  external: ["fast-fuzzy"],
  platform: "node",
  format: "esm",
  target: "node20",
  logLevel: "info",
});
