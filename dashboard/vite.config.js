// Builds straight into the Python package so `promptgauge ui` serves it (PRD F7.1).
// `emptyOutDir` would also delete the tracked `.gitkeep`, so a tiny plugin puts it back.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const OUT_DIR = resolve(__dirname, "../src/promptgauge/api/static");
const GITKEEP = join(OUT_DIR, ".gitkeep");

function keepGitkeep() {
  let content = "";
  return {
    name: "keep-gitkeep",
    buildStart() {
      content = existsSync(GITKEEP) ? readFileSync(GITKEEP, "utf8") : "";
    },
    closeBundle() {
      writeFileSync(GITKEEP, content);
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), keepGitkeep()],
  build: { outDir: OUT_DIR, emptyOutDir: true },
  server: {
    // The dev server proxies the API to a running `promptgauge ui`; `changeOrigin` rewrites the
    // Host header so HostGuard lets the request through.
    proxy: { "/api": { target: "http://127.0.0.1:7331", changeOrigin: true } },
  },
});
