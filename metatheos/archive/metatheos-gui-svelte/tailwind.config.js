/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{svelte,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        navy: {
          DEFAULT: '#374785',
          light: '#4d5d9a',
          dark: '#2a3666',
        },
        coral: {
          DEFAULT: '#F76C6C',
          hover: '#E55B5B',
        },
        cream: {
          DEFAULT: '#F8E9A1',
          hover: '#E8D991',
        },
        sky: {
          DEFAULT: '#A8D0E6',
          hover: '#98C0D6',
        },
      },
    },
  },
  plugins: [],
}
