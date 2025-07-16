import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import path, { resolve } from "path";

export default defineConfig({
  root: "./flaskr/static/",
  base: "/assets/",
  build: {
    manifest: "manifest.json",
    outDir: resolve("./flaskr/static/assets_compiled/"),
    assetsDir: "bundled",
    rollupOptions: {
      input: [
        resolve("./flaskr/static/js/main.js"),
        resolve("./flaskr/static/js/catalog/catalog.js"),
        resolve("./flaskr/static/js/trip-setup.js"),
        resolve("./flaskr/static/js/itinerary/trip-itinerary.js"),
        resolve("./flaskr/static/styles/styles.css"),
      ],
    },
    emptyOutDir: true,
    copyPublicDir: false,
  },
  plugins: [tailwindcss()],
});
