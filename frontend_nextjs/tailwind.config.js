/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        paper: 'hsl(var(--paper) / <alpha-value>)',
        'paper-2': 'hsl(var(--paper-2) / <alpha-value>)',
        ink: 'hsl(var(--ink) / <alpha-value>)',
        muted: 'hsl(var(--muted) / <alpha-value>)',
        accent: 'hsl(var(--accent) / <alpha-value>)',
      },
      fontFamily: {
        display: ['Fraunces', 'ui-serif', 'Georgia', 'serif'],
        body: [
          'Instrument Sans',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
      },
      keyframes: {
        dash: {
          '0%': { strokeDashoffset: 900 },
          '100%': { strokeDashoffset: 0 },
        },
        scan: {
          '0%': { transform: 'translateX(-30%)' },
          '100%': { transform: 'translateX(130%)' },
        },
        drift: {
          '0%': { transform: 'translate3d(0, 0, 0)' },
          '50%': { transform: 'translate3d(0, -10px, 0)' },
          '100%': { transform: 'translate3d(0, 0, 0)' },
        },
        reveal: {
          '0%': { opacity: 0, transform: 'translate3d(0, 14px, 0)' },
          '100%': { opacity: 1, transform: 'translate3d(0, 0, 0)' },
        },
      },
      animation: {
        dash: 'dash 1.8s ease-out both',
        scan: 'scan 2.6s ease-in-out infinite',
        drift: 'drift 6s ease-in-out infinite',
        reveal: 'reveal 700ms cubic-bezier(0.2, 0.8, 0.2, 1) both',
      },
      boxShadow: {
        soft: '0 18px 55px hsl(var(--shadow) / 0.14)',
      },
    },
  },
  plugins: [],
};
