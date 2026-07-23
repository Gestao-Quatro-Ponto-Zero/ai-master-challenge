import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14233a",
        muted: "#607089",
        canvas: "#f4f7fb",
        panel: "#ffffff",
        line: "#dce3ed",
        blue: "#315f8c",
        gold: "#b68433",
        orange: "#c66b3d",
        olive: "#708253",
        pink: "#a85d76"
      },
      boxShadow: {
        panel: "0 10px 30px rgba(20, 35, 58, 0.07)"
      }
    }
  },
  plugins: []
};

export default config;
