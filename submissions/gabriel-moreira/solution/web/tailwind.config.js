/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#001F35",
        gold: "#B9915B",
        bg: "#FAFBFC",
        border: "#E5E7EB",
        muted: "#64748B",
        alert: "#AF4332",
      },
      fontFamily: {
        sans: ["Manrope", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xs: "8px",
        sm: "12px",
        md: "16px",
        lg: "20px",
        xl: "24px",
      },
    },
  },
  plugins: [],
};
