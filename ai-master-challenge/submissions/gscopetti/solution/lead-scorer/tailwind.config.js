/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hubspot: {
          orange: '#FF5630',
          dark: '#1F2937',
          gray: {
            100: '#F3F4F6',
            200: '#E5E7EB',
          },
          peach: '#FCE7D5',
          black: '#111111',
        }
      },
      borderRadius: {
        'hb': '8px',
      }
    },
  },
  plugins: [],
}
