/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        workspace: {
          bg: '#f8fafc', // soft warm off-white / light slate workspace
          subtle: '#f1f5f9', // slightly darker shell background
          card: '#ffffff', // pure white card surface
          cardElevated: '#ffffff',
          border: '#e2e8f0', // soft border
          borderSubtle: '#edf2f7',
        },
        ink: {
          900: '#0f172a', // dark charcoal primary text
          800: '#1e293b', // secondary dark text
          700: '#334155', // muted text
          600: '#475569',
          500: '#64748b', // tertiary muted
          400: '#94a3b8',
          300: '#cbd5e1',
          200: '#e2e8f0',
          100: '#f1f5f9',
          50: '#f8fafc',
        },
        clinical: {
          teal: '#0d9488', // restrained teal
          tealLight: '#f0fdfa',
          tealBorder: '#ccfbf1',
          cyan: '#0284c7', // restrained sky/cyan
          cyanLight: '#f0f9ff',
          blue: '#2563eb', // soft blue
          blueLight: '#eff6ff',
          purple: '#6366f1', // analysis accent
          purpleLight: '#eef2ff',
          amber: '#d97706', // warning amber
          amberLight: '#fffbeb',
          rose: '#e11d48', // critical red
          roseLight: '#fff1f2',
          emerald: '#059669', // success green
          emeraldLight: '#ecfdf5',
        },
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          500: '#0d9488',
          600: '#0f766e',
          700: '#115e59',
          900: '#134e4a',
        },
      },
    },
  },
  plugins: [],
}
