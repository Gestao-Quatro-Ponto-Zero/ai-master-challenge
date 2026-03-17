import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#af4332',
          hover: '#842E20',
        },
        secondary: '#0f1a45',
        accent: '#b9915b',
        bg: '#fafbfc',
        fade: '#F5F4F3',
        surface: '#ffffff',
        'text-main': '#001f35',
        'text-muted': '#60708a',
        border: '#e5e7eb',
        success: '#25D366',
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        ui: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Libre Baskerville', 'Georgia', 'serif'],
      },
      fontSize: {
        display: ['42px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        h2: ['36px', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        h3: ['28px', { lineHeight: '1.3' }],
        h4: ['22px', { lineHeight: '1.4' }],
        h5: ['18px', { lineHeight: '1.4' }],
        body: ['16px', { lineHeight: '1.6' }],
        sm: ['14px', { lineHeight: '1.5' }],
        xs: ['13px', { lineHeight: '1.4', letterSpacing: '0.01em' }],
      },
      borderRadius: {
        sm: '5px',
        md: '10px',
        lg: '16px',
        xl: '20px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 2px 8px rgba(0, 0, 0, 0.06)',
        md: '0 0 22px 0 rgba(0, 0, 0, 0.14)',
        lg: '6px 6px 9px rgba(0, 0, 0, 0.20)',
        xl: '12px 12px 50px rgba(0, 0, 0, 0.40)',
      },
      maxWidth: {
        content: '800px',
        wide: '1200px',
      },
    },
  },
  plugins: [],
}

export default config
