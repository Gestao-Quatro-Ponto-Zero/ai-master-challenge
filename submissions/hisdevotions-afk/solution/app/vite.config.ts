import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base relativa: o mesmo build roda na raiz do GitHub Pages, numa subpasta ou via `vite preview`.
export default defineConfig({ base: "./", plugins: [react()] });
