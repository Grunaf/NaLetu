import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
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
  plugins: [tailwindcss()],
});
