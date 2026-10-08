import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    // Bind mounts from Windows/macOS hosts do not deliver inotify events into the container.
    watch:
      process.env.VITE_USE_POLLING === "true" ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
});
