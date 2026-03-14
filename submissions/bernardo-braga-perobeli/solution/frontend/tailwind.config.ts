import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: { DEFAULT: "#0f172a", hover: "#1e293b", active: "#334155" },
        sev: { baixo: "#22c55e", medio: "#eab308", critico: "#ef4444" },
      },
    },
  },
  plugins: [],
};

export default config;
