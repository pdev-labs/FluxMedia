import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Single-file-ish output: one JS + one CSS bundle so the Python server
  // can embed them as PORTAL_JS / PORTAL_CSS (served at /app.js, /style.css).
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsInlineLimit: 100000000,
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks: undefined,
        inlineDynamicImports: true,
        entryFileNames: "app.js",
        assetFileNames: (info) =>
          info.name?.endsWith(".css") ? "style.css" : "assets/[name][extname]",
      },
    },
  },
});
