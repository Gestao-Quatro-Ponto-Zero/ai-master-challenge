import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Hosts extras liberados no servidor de desenvolvimento (ex.: acesso por rede interna): VITE_ALLOWED_HOSTS=host1,host2
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS ?? "").split(",").map((h) => h.trim()).filter(Boolean);

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: { host: "0.0.0.0", port: 5180, allowedHosts },
  preview: { host: "0.0.0.0", port: 5180, allowedHosts },
});
