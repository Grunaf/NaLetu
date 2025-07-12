import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    manifest: "manifest.json",
    outDir: resolve("./flaskr/static/assets"),
    rollupOptions: {
      input: {
        test: resolve("./flaskr/static/js/main.js"),
      },
    },
  },
});
