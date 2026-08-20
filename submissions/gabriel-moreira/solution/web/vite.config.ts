import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxy /api -> a API FastAPI local durante o desenvolvimento (task 5.1).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
