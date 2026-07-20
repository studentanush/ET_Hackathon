import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Proxy /api to the FastAPI backend so the app uses same-origin relative URLs.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5175,
    proxy: {
      "/api": {
        target: process.env.SITEMIND_API || "http://127.0.0.1:8141",
        changeOrigin: true,
      },
    },
  },
});
